from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import suppress
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Iterator,
    Literal,
    Mapping,
    Protocol,
    Type,
    TypeAlias,
    TypeVar,
    assert_never,
    cast,
    get_args,
    runtime_checkable,
)

from typing_extensions import override

from lib.decimal_tools import DecimalRange, SupportsDecimal, roll_decimal
from lib.sentinel import Sentinel
from src.char.xp import ExponentialLevelSystem


@runtime_checkable
class SupportsGetValue(Protocol):
    @abstractmethod
    def get_value(self) -> Decimal: ...


class DynamicValue(SupportsGetValue):

    def __init__(self,
                 dynamic_source: SupportsGetValue,
                 multiplier: SupportsDecimal = Decimal('1.0'),
                 ) -> None:

        self._dynamic_source = dynamic_source
        self._multiplier = Decimal(multiplier)

    def get_value(self) -> Decimal:
        return self._dynamic_source.get_value() * self._multiplier


class ConstValue(SupportsGetValue):

    __stored: ClassVar[dict[Decimal, ConstValue]] = {}

    def __init__(self, value: SupportsDecimal) -> None:
        self._value = Decimal(value)

    def __new__(cls, _value: SupportsDecimal) -> ConstValue:
        _value = Decimal(_value)

        try:
            return ConstValue.__stored[_value]
        except KeyError:
            instance = object.__new__(cls)
            ConstValue.__init__(instance, _value)
            ConstValue.__stored[_value] = instance

            return instance

    def get_value(self) -> Decimal:
        return self._value


class Modification(Enum):

    FLAT = 1
    PERCENT_ADDITIVE = 2
    PERCENT_MULTIPLICATIVE = 3


Order: TypeAlias = Literal[0, 1, 2, 3, 4, 5]
ORDER_VALUES: tuple[Order, ...] = get_args(Order)


class Modifier(SupportsGetValue):

    """
    Modifiers are used to modify values of stats. The order in which modifiers should
    be applied is represented by their `order` values (modifiers with the lower order
    values are supposed to be applied first).

    Modifiers can be of different type, represented by their `modification` type:
        - `FLAT` modifier simply adds its value to the modified object's value.
        - `PERCENT_ADDITIVE` modifiers stack together (assuming they have the same order
        value, which would be true by default), then the modified object's value is
        multiplied by the result sum.
        - `PERCENT_MULTIPLICATIVE` modifier immediately multiplies the modified object's
        value by the modifier's value.

    Note that the value of a percent modifier is added to 1.0 before making the actual
    multiplication.

    ```Python
    stat_ = Stat(_base=10)
    stat_.value
    >>> 10
    stat_.add_modifier(
        Modifier(_base=0.5, _modification=Modification.PERCENT_MULTIPLICATIVE))
    stat_.value
    >>> 15
    ```

    In order to create debuffs, provide modifiers with negative bases.

    ```Python
    stat_ = Stat(_base=10)
    stat_.add_modifier(Modifier(-0.5, Modification.PERCENT_MULTIPLICATIVE))
    stat_.value
    >>> 5
    ```

    A modifier can also take any object with a `value` property as its base. In this case
    this object's value will be used as the modifier's value.

    ```Python
    base = GenericValue(10)
    modifier = Modifier(base, Modification.FLAT)

    modifier.value
    >>> 10

    base.value += 1
    modifier.value
    >>> 11
    ```
        """

    def __init__(self,
                 base: SupportsGetValue | SupportsDecimal,
                 modification: Modification,
                 order: Order | None = None,
                 source: object | None = None,
                 ) -> None:
        """
        @params
            - _base: The base which defines the modifier's value. If it's an object with
            a `value` property, the modifier's value is equal to this object's value
            and therefore can be updated. If it's a constant, the modifier will always
            return the same value. Negative modifiers (debuffs) are created by making
            the base negative. Percent modifiers work with the actual base value: for
            instance, a percent modifier with the base equal to 0.5 will increase its
            modified object's value by 50% (to 150%).

            - _modification: The type of modification which defines how the value of a
            modified object will be affected.
                - `FLAT` modifier adds the modifier's value to the object's value.
                - `PERCENT_ADDITIVE` modifiers of the same order are summed together and
                then the object's value is multiplied by their result value.
                - `PERCENT_MULTIPLICATIVE` modifier multiplies the object's value by the
                modifier's value.

            - _order: A number from zero to five that determines the order in which the
            modifiers are applied to the modified object (modifiers with the lower order
            are applied first). If not given, the _modification's value is used, where
            `FLAT` is 1, `PERCENT_ADDITIVE` is 2, and `PERCENT_MULTIPLICATIVE` is 3.
            There is usually no need to override the default behaviour.

            - _source: Any object (e.g., a status token) which represents the source the
            modifier comes from.
            """

        self._base = base if isinstance(
            base, SupportsGetValue) else ConstValue(Decimal(base))

        self._modification = modification

        assert self._modification.value in ORDER_VALUES, (
            "Inappropriate modification value, expected to be in"
            f"{str(ORDER_VALUES)}, but became {self._modification.value}.")
        self._order: Order = order if order is not None else self._modification.value

        self._source = source

    @property
    def order(self) -> Order:
        return self._order

    @property
    def source(self) -> object:
        return self._source

    @property
    def modification(self) -> Modification:
        return self._modification

    def get_value(self) -> Decimal:
        return self._base.get_value()


class Stat(SupportsGetValue, ABC):

    def __init__(self, base: SupportsDecimal) -> None:
        self._base = Decimal(base)
        self._modifiers: list[Modifier] = []

    @property
    def base(self) -> Decimal:
        return self._base

    @base.setter
    def base(self, new_value: SupportsDecimal) -> None:
        self._set_base(Decimal(new_value))

    @property
    def modifiers(self) -> tuple[Modifier, ...]:
        return tuple(self._modifiers)

    def get_value(self, optional_modifiers: list[Modifier] | None = None) -> Decimal:
        if optional_modifiers:
            modifiers = self._modifiers + optional_modifiers
            modifiers.sort(key=lambda m: m.order)
        else:
            modifiers = self._modifiers

        value = self._calculate_modified_value(modifiers)
        return self._adjusted_value(value)

    # def calculate_value_with_temporary_modifiers(self, temporary_modifiers: list[Modifier]) -> Decimal:
    #     modifiers = self._modifiers + temporary_modifiers
    #     modifiers.sort(key=lambda m: m.order)
    #     value = self._calculate_modified_value(modifiers)
    #     return self._adjusted_value(value)

    def add_modifier(self, modifier: Modifier) -> None:
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.order)

    def remove_modifier(self, modifier: Modifier) -> None:
        self._modifiers.remove(modifier)

    def remove_source(self, source: object) -> None:
        self._modifiers = [
            modifier for modifier in self._modifiers if modifier.source != source]

    @abstractmethod
    def _adjusted_value(self, value: Decimal) -> Decimal:
        return value

    @abstractmethod
    def _set_base(self, new_value: SupportsDecimal) -> None:
        self._base = Decimal(new_value)

    def _calculate_modified_value(self, modifiers: list[Modifier]) -> Decimal:
        value = self.base
        sum_percent_additive = Decimal(0)

        for i, modifier in enumerate(modifiers):
            if modifier.modification is Modification.FLAT:
                value += modifier.get_value()

            elif modifier.modification is Modification.PERCENT_ADDITIVE:
                sum_percent_additive += modifier.get_value()

                # Keep increasing the sum while there are percent additive modifiers.
                with suppress(IndexError):
                    if modifiers[i+1].modification is Modification.PERCENT_ADDITIVE:
                        continue

                value *= Decimal(1) + sum_percent_additive
                sum_percent_additive = Decimal(0)

            elif modifier.modification is Modification.PERCENT_MULTIPLICATIVE:
                value *= Decimal(1) + modifier.get_value()

            else:
                assert_never(modifier.modification)

        return value


class BoundedStat(Stat):

    def __init__(self,
                 base: SupportsDecimal,
                 lower_bound: SupportsDecimal | None,
                 upper_bound: SupportsDecimal | None,
                 modified_upper_bound: SupportsDecimal | None,
                 ) -> None:

        if upper_bound is None and modified_upper_bound is not None:
            raise ValueError(
                "Stat upper bound cannot be None type if modified upper bound is given.")

        super().__init__(base)
        self._lower_bound = lower_bound if lower_bound is None else Decimal(
            lower_bound)
        self._upper_bound = upper_bound if upper_bound is None else Decimal(
            upper_bound)
        self._modified_upper_bound = modified_upper_bound if modified_upper_bound is None else Decimal(
            modified_upper_bound)

        if any([not self._lower_bound is None and self._base < self._lower_bound,
                not self._upper_bound is None and self._base > self._upper_bound]):
            raise ValueError(f"Stat base is out of bounds (expected the base to be in "
                             f"[{self._lower_bound}-{self._upper_bound}] range, got {self._base} instead.")

        if self._modified_upper_bound is not None:
            assert self._upper_bound is not None
            if self._modified_upper_bound < self._upper_bound:
                raise ValueError("Modified upper bound cannot be less than upper bound"
                                 f"(Got modified = {modified_upper_bound}, standard = {upper_bound})")

    def is_capped(self) -> bool:
        return self._upper_bound is not None and self._base >= self._upper_bound

    def _adjust_base(self) -> None:
        self._base = self._adjust_for_bounds(
            self._base, self._lower_bound, self._upper_bound)

    @override
    def _adjusted_value(self, value: Decimal) -> Decimal:
        return self._adjust_for_bounds(value, self._lower_bound, self._modified_upper_bound)

    def _adjust_for_bounds(self, value: Decimal, lower_bound: Decimal | None, upper_bound: Decimal | None) -> Decimal:
        if lower_bound is not None:
            value = max(value, lower_bound)
        if upper_bound is not None:
            value = min(value, upper_bound)
        return value

    @override
    def _set_base(self, new_value: SupportsDecimal) -> None:
        super()._set_base(Decimal(new_value))
        self._adjust_base()


class PrimaryStat(BoundedStat):

    _LOWER_BOUND_DEFAULT: ClassVar = Decimal(0)
    _UPPER_BOUND_DEFAULT: ClassVar = Decimal(100)
    _MODIFIED_UPPER_BOUND_DEFAULT: ClassVar = Decimal(125)

    def __init__(self,
                 base: SupportsDecimal,
                 lower_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 modified_upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 ) -> None:

        lower_bound = self._LOWER_BOUND_DEFAULT if lower_bound is Sentinel.NOT_GIVEN else lower_bound
        upper_bound = self._UPPER_BOUND_DEFAULT if upper_bound is Sentinel.NOT_GIVEN else upper_bound
        modified_upper_bound = self._MODIFIED_UPPER_BOUND_DEFAULT if modified_upper_bound is Sentinel.NOT_GIVEN else modified_upper_bound

        super().__init__(base, lower_bound, upper_bound, modified_upper_bound)


class SecondaryStat(BoundedStat):

    def __init__(self,
                 base: SupportsDecimal,
                 lower_bound: SupportsDecimal | None = Decimal(0),
                 upper_bound: SupportsDecimal | None = None,
                 modified_upper_bound: SupportsDecimal | None = None,
                 ) -> None:

        super().__init__(base, lower_bound, upper_bound, modified_upper_bound)


class Defence(SecondaryStat):

    def __init__(self, _base: SupportsDecimal) -> None:
        super().__init__(_base, lower_bound=None,
                         upper_bound=None, modified_upper_bound=None)


class Resist(SecondaryStat):

    def __init__(self,
                 base: SupportsDecimal,
                 base_max: SupportsDecimal | None = None,
                 growth: SupportsDecimal = Decimal(0),
                 growth_max: SupportsDecimal = Decimal(0),
                 ) -> None:

        base = DecimalRange(base, base_max).get_random_value(
        ) if base_max is not None else Decimal(base)
        super().__init__(base, lower_bound=Decimal(0), upper_bound=None)
        self._growth = DecimalRange(growth, growth_max)

        if self._growth.lower < 0 or self._growth.upper < 0:
            raise ValueError("Growth value cannot be less than zero.")

    def grow(self) -> Decimal:
        before = self.base
        self.base += self._growth.get_random_value()
        after = self.base

        assert after - before >= 0
        return after - before


class DamageReduction(SecondaryStat):

    def __init__(self, base: SupportsDecimal) -> None:
        super().__init__(base, lower_bound=0, upper_bound=None, modified_upper_bound=None)


class LoadStatus(Enum):

    WHITE = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    RED = 5


class CarryingCapacity(SecondaryStat):

    __LOAD_LEVELS: ClassVar = {
        Decimal('1.0'): LoadStatus.RED,
        Decimal('0.8'): LoadStatus.YELLOW,
        Decimal('0.6'): LoadStatus.GREEN,
        Decimal('0.4'): LoadStatus.BLUE,
        Decimal('0.0'): LoadStatus.WHITE,
    }

    def __init__(self, base: SupportsDecimal) -> None:
        super().__init__(base, lower_bound=Decimal(0),
                         upper_bound=None, modified_upper_bound=None)
        self._load = Decimal(0)

    def __str__(self) -> str:
        return f"{self.load}/{self.get_value()} lb"

    @property
    def load(self) -> Decimal:
        return self._load

    @load.setter
    def load(self, new_value: SupportsDecimal) -> None:
        self._load = self._adjusted_value(Decimal(new_value))

    @property
    def load_status(self) -> LoadStatus:
        if self.get_value() == Decimal(0):
            return LoadStatus.RED if self.load > Decimal(0) else LoadStatus.WHITE

        load_percent = self.load / self.get_value()

        assert self.load >= Decimal(0)
        # Ensure the dictionary is sorted from max to min.
        assert list(self.__LOAD_LEVELS.keys()) == list(
            sorted(self.__LOAD_LEVELS.keys()))[::-1]

        return next((load_status for step, load_status in self.__LOAD_LEVELS.items() if load_percent >= step), LoadStatus.WHITE)


class ResourceRegeneration(SecondaryStat):

    def __init__(self, base: SupportsDecimal) -> None:
        super().__init__(base, lower_bound=Decimal(0),
                         upper_bound=None, modified_upper_bound=None)


# class ResourceDrained(Exception):
#     pass


class Resource(SecondaryStat):

    def __init__(self,
                 base: SupportsDecimal,
                 base_max: SupportsDecimal | None = None,
                 regeneration: SupportsDecimal | ResourceRegeneration = Decimal(
                     0),
                 growth: SupportsDecimal = Decimal(0),
                 growth_max: SupportsDecimal = Decimal(0),
                 lower_bound: SupportsDecimal | None = Decimal(0),
                 upper_bound: SupportsDecimal | None = None,
                 modified_upper_bound: SupportsDecimal | None = None,
                 ) -> None:

        base = DecimalRange(base, base_max).get_random_value(
        ) if base_max is not None else Decimal(base)
        super().__init__(base, lower_bound, upper_bound, modified_upper_bound)
        self._growth = DecimalRange(growth, growth_max)
        self._regeneration = regeneration if isinstance(
            regeneration, ResourceRegeneration) else ResourceRegeneration(regeneration)
        self._current = self._base

        # self._aware_of_resource_drain = False if self._current > Decimal(
        #     0) else True

    def __str__(self) -> str:
        return f"{self.current}/{self.get_value()}"

    @property
    def current(self) -> Decimal:
        #     # Required because values of modifiers may change.
        self._update_current()
        return self._current

    @current.setter
    def current(self, new_value: SupportsDecimal) -> None:
        self._current = Decimal(new_value)
        # self._update_current()

    @property
    def regeneration(self) -> ResourceRegeneration:
        return self._regeneration

    @override
    def add_modifier(self, modifier: Modifier, regeneration: bool = False) -> None:
        if regeneration:
            self.regeneration.add_modifier(modifier)
        else:
            super().add_modifier(modifier)

    @override
    def remove_modifier(self, modifier: Modifier, regeneration: bool = False) -> None:
        if regeneration:
            self.regeneration.remove_modifier(modifier)
        else:
            super().remove_modifier(modifier)

    @override
    def remove_source(self, source: object) -> None:
        super().remove_source(source)
        self.regeneration.remove_source(source)

    # @override
    # def add_modifier(self, modifier: Modifier) -> None:
    #     super().add_modifier(modifier)
    #     self._update_current()

    def grow(self) -> Decimal:
        before = self.base
        self.base += self._growth.get_random_value()
        after = self.base

        assert after - before >= 0

        return after - before

    def regenerate(self) -> Decimal:
        before = self.current
        self.current += self.regeneration.get_value()
        after = self.current

        assert after - before >= 0

        return after - before

    # @override
    # def remove_modifier(self, modifier: Modifier) -> None:
    #     super().remove_modifier(modifier)
        # self._update_current()

    # @override
    # def remove_source(self, source: object) -> None:
    #     super().remove_source(source)
        # self._update_current()

    # @override
    # def _adjust_base(self) -> None:
    #     super()._adjust_base()
        # self._update_current()

    def _update_current(self) -> None:
        self._current = self._adjust_for_bounds(
            self._current, self._lower_bound, self.get_value())

        # if self._lower_bound is not None \
        #         and self._current <= self._lower_bound \
        #         and not self._aware_of_resource_drain:
        #     self._aware_of_resource_drain = True
        #     raise ResourceDrained

        # if self._lower_bound is not None \
        #         and self._current > self._lower_bound:
        #     self._aware_of_resource_drain = False


class Armour(Resource):

    def __init__(self,
                 base: SupportsDecimal,
                 base_max: SupportsDecimal | None = None,
                 regeneration: SupportsDecimal | ResourceRegeneration = Decimal(
                     0),
                 growth: SupportsDecimal = Decimal(0),
                 growth_max: SupportsDecimal = Decimal(0),
                 ) -> None:

        super().__init__(base, base_max, regeneration, growth, growth_max,
                         lower_bound=None, upper_bound=None, modified_upper_bound=None)


class Skill(PrimaryStat, ExponentialLevelSystem):

    def __init__(self,
                 base: SupportsDecimal,
                 scale: SupportsDecimal,
                 lower_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 modified_upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 ) -> None:

        super().__init__(base, lower_bound, upper_bound, modified_upper_bound)
        ExponentialLevelSystem.__init__(self, scale)

    @property
    def level(self) -> int:
        return int(self.base)

    @override
    def add_xp(self, amount: int) -> None:
        if self.is_capped():
            return

        super().add_xp(amount)
        while self.can_levelup():
            self.levelup()

    @override
    def can_levelup(self) -> bool:
        if self.is_capped():
            return False

        return super().can_levelup()

    @override
    def levelup(self) -> None:
        if not self.can_levelup():
            return

        self.base += 1

    @override
    def _set_base(self, new_value: SupportsDecimal) -> None:
        super()._set_base(new_value)
        self._refresh_xp()


class DamageBonus(BoundedStat):

    def __init__(self, base: SupportsDecimal) -> None:
        super().__init__(base, lower_bound=Decimal(0),
                         upper_bound=None, modified_upper_bound=None)


class Damage(BoundedStat):

    def __init__(self, base: SupportsDecimal, bonus: SupportsDecimal | None = None) -> None:
        super().__init__(base, lower_bound=Decimal(0),
                         upper_bound=None, modified_upper_bound=None)
        self._bonus = DamageBonus(
            bonus) if bonus is not None else DamageBonus(Decimal(0))

    @property
    def bonus(self) -> DamageBonus:
        return self._bonus

    def roll(self, optional_modifiers: list[Modifier] | None) -> Decimal:
        damage_min = self.get_value(optional_modifiers)
        damage_max = damage_min + self.bonus.get_value(optional_modifiers)
        return roll_decimal(damage_min, damage_max)

    @override
    def add_modifier(self, modifier: Modifier, bonus: bool = False) -> None:
        if bonus:
            self.bonus.add_modifier(modifier)
        else:
            super().add_modifier(modifier)

    @override
    def remove_modifier(self, modifier: Modifier, bonus: bool = False) -> None:
        if bonus:
            self.bonus.remove_modifier(modifier)
        else:
            super().remove_modifier(modifier)

    @override
    def remove_source(self, source: object) -> None:
        super().remove_source(source)
        self.bonus.remove_source(source)


class PrimaryStatType(Enum):

    STRENGTH = "STR"
    WILL = "WIL"
    INTELLIGENCE = "INT"
    DEXTERITY = "DEX"
    SPEED = "SPD"
    VITALITY = "VIT"
    CHARISMA = "CHA"
    PERCEPTION = "PER"


class SkillType(Enum):

    SINGLE_HANDED = "Single-handed"
    RANGED = "Ranged"
    TWO_HANDED = "Two-handed"
    DUAL_WIELDING = "Dual wielding"
    DEFENDING = "Defending"
    ORATORY = "Oratory"
    WIZARDRY = "Wizardry"
    AXE = "Axe"
    BLUNT = "Blunt"
    GREATSWORD = "Greatsword"
    SWORD = "Sword"
    POLEARM = "Polearm"
    DAGGER = "Dagger"
    STAFF_WAND = "Staff and wand"
    THROWING = "Throwing"
    BOW = "Bow"
    MARTIAL_ARTS = "Martial arts"
    SHIELD = "Shield"
    ARMOURER = "Armourer"
    FIREARM = "Firearm"
    DIVINITY = "Divinity"
    PRIMEVALITY = "Primevality"
    SORCERY = "Sorcery"
    NECROMANCY = "Necromancy"
    ILLUSIONS = "Illusions"
    LOCKPICKING = "Lockpicking"
    PICKPOCKETING = "Pickpocketing"
    STEALTH = "Stealth"
    PARRYING = "Parrying"
    CRITICAL = "Critical"
    ALCHEMY = "Alchemy"
    ENGINEERING = "Engineering"
    MUSIC = "Music"
    ARTEFACTS = "Artefacts"
    DIPLOMACY = "Diplomacy"
    LORE_KNOWLEDGE = "Lore knowledge"
    SCOUTING = "Scouting"
    SWIMMING = "Swimming"
    BEAR = "Bear"
    LAMB = "Lamb"
    CROW = "Crow"
    FOX = "Fox"
    FALCON = "Falcon"
    TORTOISE = "Tortoise"
    PANDA = "Panda"
    BAT = "Bat"

    @staticmethod
    def mastery_skills() -> tuple[SkillType, ...]:
        return (SkillType.BEAR, SkillType.LAMB, SkillType.CROW, SkillType.FOX,
                SkillType.FALCON, SkillType.TORTOISE, SkillType.PANDA, SkillType.BAT)


class DamageSource(Enum):

    PHYSICAL = "Physical"

    AIR = "Air"
    EARTH = "Earth"
    FIRE = "Fire"
    WATER = "Water"

    CURSE = "Curse"
    DISEASE = "Disease"
    MENTAL = "Mental"


class SecondaryStatType(Enum):

    ACCURACY = "ACC"
    ACTION_SPEED = "ACTSP"
    ATTACK_SPEED = "ASP"
    ATTRACTIVENESS = "ATTRACT"
    CRIT_CHANCE = "CCH"
    CRIT_DMG = "CDMG"
    DODGING = "DDG"
    INITIATIVE = "INIT"
    PENETRATION = "PEN"
    PERSUASION = "PRS"
    SPELLCASTING = "SPL"


class ResourceType(Enum):

    HIT_POINTS = "HP"
    STAMINA_POINTS = "SP"
    MANA_POINTS = "MP"


# ST = TypeVar("ST", PrimaryStatType, SkillType,
#              SecondaryStatType, ResourceType, DamageSource)
ST = TypeVar("ST")
S = TypeVar("S", bound=Stat)


class StatBlock(Mapping[ST, S]):

    def __init__(self, stats: dict[ST, S]) -> None:
        self._stats: dict[ST, S] = stats

    def __getitem__(self, __key: ST) -> S:
        return self._stats[__key]

    def __iter__(self) -> Iterator[ST]:
        return self._stats.__iter__()

    def __len__(self) -> int:
        return len(self._stats)

    def __new__(cls, *args: Any, **kwargs: Any) -> StatBlock[ST, S]:
        if cls is StatBlock:
            raise TypeError("Direct instantion of StatBlock is forbidden.")

        instance = object.__new__(cls)
        cls.__init__(instance, *args, **kwargs)
        return instance

    def remove_source(self, source: object) -> None:
        for stat_ in self._stats.values():
            stat_.remove_source(source)


class PrimaryStatBlock(StatBlock[PrimaryStatType, PrimaryStat]):
    pass


class SkillBlock(StatBlock[SkillType, Skill]):
    pass


class SecondaryStatBlock(StatBlock[SecondaryStatType, SecondaryStat]):
    pass


class ResourceBlock(StatBlock[ResourceType, Resource]):
    pass


class ArmourBlock(StatBlock[DamageSource, Armour]):
    pass


class DamageReductionBlock(StatBlock[DamageSource, DamageReduction]):
    pass


class DefenceBlock(StatBlock[DamageSource, Defence]):
    pass


class ResistBlock(StatBlock[DamageSource, Resist]):
    pass


class DamageBlock(StatBlock[DamageSource, Damage]):
    pass


SB = TypeVar("SB", bound=StatBlock[Any, Any])


class StatSheet:

    def __init__(self, *blocks: StatBlock[Any, Any]) -> None:
        self._blocks = {type(block): block for block in blocks}

    def __iter__(self) -> Iterator[StatBlock[Any, Any]]:
        return self._blocks.values().__iter__()

    def add(self, block: SB) -> None:
        self._blocks[type(block)] = block

    def get(self, block: Type[SB]) -> SB:
        # The keys are always supposed to be the types of values.
        return cast(SB, self._blocks[block])

    def remove_source(self, source: object) -> None:
        for block in self._blocks.values():
            block.remove_source(source)


# class StatDraft(TypedDict):

#     _base: SupportsDecimal
#     _base_max: SupportsDecimal | None
#     _lower_bound: SupportsDecimal | None
#     _upper_bound: SupportsDecimal | None
#     _modified_upper_bound: SupportsDecimal | None
#     _scale: SupportsDecimal
#     _regeneration: SupportsDecimal | ResourceRegeneration
#     _growth: SupportsDecimal
#     _growth_max: SupportsDecimal


# class StatSheetDraft(TypedDict):

#     _primary_stats: dict[str, StatDraft]
#     _skills: dict[str, StatDraft]
#     _secondary_stats: dict[str, StatDraft]
#     _resources: dict[str, StatDraft]

#     _armour: dict[str, StatDraft]
#     _damage_reduction: dict[str, StatDraft]
#     _defence: dict[str, StatDraft]
#     _resist: dict[str, StatDraft]
