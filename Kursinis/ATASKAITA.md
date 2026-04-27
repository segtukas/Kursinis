# Kursinis darbas: F1 stiliaus lenktynių žaidimas (Pygame)

**Formatas:** Markdown (LT)  
**Projekto katalogas:** `Documents/Universitetas/Kursinis/`

---

## 1. Įvadas

### 1a. Kursinio tikslas ir tema

Tikslas — sukurti **interaktyvią F1 tematikos lenktynių demonstraciją** su karjeros elementais: vairuotojo kūrimas, komandos pasirinkimas, kvalifikacija, lenktynės, rezultatai, progresija (pinigai, mašinos tobulinimas, upgrade tokenai). Tema derinama su 2025 F1 sezono komandomis ir vairuotojais.

### 1b. Kas yra programa?

Tai **desktop žaidimas**, parašytas **Python** kalba su **Pygame**. Pagrindinis vykdomasis failas yra monolitinis `import pygame.py` (didelis vienas modulis su žaidimo ciklu ir piešimu). Papildomai logika ir duomenys išskaidyti į paketą **`f1_game/`** (OOP, šablonai, testuojami moduliai, JSON saugojimas).

### 1c. Kaip paleisti programą?

1. Įdiekite **Python 3** ir **pygame** (`pip install pygame`).
2. Terminale:

```bash
python3 "/Users/kajuszeynalov/Documents/Universitetas/Kursinis/import pygame.py"
```

Arba:

```bash
cd "/Users/kajuszeynalov/Documents/Universitetas/Kursinis"
python3 "import pygame.py"
```

*(Atkreipkite dėmesį į **tarpą** faile `import pygame.py` — reikia kabučių.)*

### 1d. Kaip naudoti programą?

Trumpai: sekite ekrano būsenas — **TITLE** → **MAIN_MENU** / **CHARACTER_CREATION** → komandos „case“ → **SPONSOR_OFFERS** → **PROFILE**, iš ten **START SEASON** → **PRE_RACE** / **QUALIFYING** → **RACE_SETUP** → **RACE** → rezultatai ir **CHEST_REWARD**.

**Progreso failas:** žaidimas automatiškai bando įkelti iš `saves/career_progress.json`. Rankiniu būdu: **F5** — išsaugoti, **F9** — įkelti (žr. kodo skyrių apie failų I/O).

**Testai (reikalavimas 5):**

```bash
cd "/Users/kajuszeynalov/Documents/Universitetas/Kursinis"
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 2. Tyrimas / analizė: įgyvendinimas ir ryšys su reikalavimais

Žemiau — kur **konkrečiai kode** įgyvendinti dėstytojo reikalavimai (su ištraukomis).

### 2.0 Veiksmai ir naudojami būdai (žodinė santrauka)

Čia trumpai, **žodžiais**: kokiam žaidimo ar programos veiksmui kokį **techninį būdą** naudojame (be gilėjimo į kiekvieną funkciją).

| Kas vyksta (veiksmas) | Kokį būdą naudojame |
|------------------------|----------------------|
| Langas, klaviatūra, pelė, animacija kiekviename kadre | **Pygame** biblioteka: inicializacija (`pygame.init`), langas (`set_mode`), begalinis **žaidimo ciklas** (`while`), kiekvieno kadro **įvykių apdorojimas** (`pygame.event`) ir **piešimas** ant paviršiaus (`blit`, `draw`, šriftai). |
| Perėjimas tarp titulo, meniu, kūrimo, lenktynių ir t. t. | **Būsenų valdymas**: vienas kintamasis (pvz. `game_state`) nusako, kuri „scena“ aktyvi; pagal ją skiriasi piešimo ir įvykių šakos — tai paprasta **būsenų mašina**, ne atskiros programos. |
| Komandų, vairuotojų, statistikų parodymas žaidime | **Duomenų moduliai** (`game_data.py`, `f1_game/driver_data.py` ir pan.): duomenys laikomi Python struktūrose (žodynai, sąrašai), importuojami į pagrindinį failą ir ten naudojami UI bei logikai. |
| Sezono eiga, GP, trasos kontūras | **Kalendoriaus ir trasos duomenys** atskiruose moduliuose (`f1_game/season_calendar.py`, `f1_game/track_seed_data.py`, GeoJSON failai `tracks/`), o interaktyvi lenktynių / kvalifikacijos eiga daugiausia susieta su `import pygame.py` (funkcijos su `qual_*`, `race_*` ir pan.). |
| Po lenktynių: dėžė su pinigais ir upgrade pagal finišo vietą | **Objektinis programavimas** ir **Factory Method** (`f1_game/oop_rewards.py`): pagal vietą sukuriamas konkretus „taisyklių“ objektas, paslauga (`ChestRewardService`) surenka prizą; pagrindinis failas tik **kviečia** šią paslaugą (`DEFAULT_CHEST_REWARD_SERVICE`), vietoj ilgos `if/elif` grandinės rezultatų ekrane. |
| Išsaugoti / įkelti karjerą (pinigai, mašina, sezonas) | **Kompozicija** viename „momentinėje nuotraukoje“ objekte (`CareerSnapshot`), **agregacija** per valdytoją (`CareerDataManager`) ir **JSON failas** diske (`JsonSnapshotSerializer`). Rankinis valdymas: klavišai **F5** (rašymas) ir **F9** (skaitymas). |
| Patikrinti, ar chest taisyklės ir saugojimas veikia teisingai | **`unittest`**: atskiri testų failai `tests/` tikrina gamyklą, apdovanojimus ir JSON „įrašyk–perskaityk“ ciklą be Pygame lango. |
| Laikyti švarų modulinį kodą | **`pyproject.toml` + Ruff** (PEP8 kryptimi) taikomas paketui `f1_game/` ir `tests/`; didysis `import pygame.py` sąmoningai **neformatuojamas masiniu būdu**, kad nekiltų didelio refaktoriaus rizika. |

Trumpai tariant: **Pygame + būsenų perėjimai** valdo žaidimą ekrane; **atskiri moduliai** laiko F1 duomenis, kalendorių ir trasas; **OOP + Factory + servisas** valdo po lenktynių prizus; **JSON + manager/serializer** valdo išsaugojimą; **`unittest` ir Ruff** — atitinkamai testams ir stiliui moduliniuose failuose.

### 2.1 Keturi OOP stulpai (abstrakcija, paveldėjimas, polimorfizmas, enkapsuliacija)

**Vieta:** `f1_game/oop_rewards.py`

- **Abstrakcija:** abstrakti bazinė klasė `ChestTierRule` su `@abstractmethod matches(...)`.
- **Paveldėjimas:** `SilverChestRule`, `GoldenChestRule`, … paveldi `ChestTierRule`.
- **Polimorfizmas:** skirtingos taisyklės turi tą patį „kontraktą“ (`matches`, `roll_reward`), naudojami per bendrą tipą.
- **Enkapsuliacija:** vidiniai parametrai (`_tier`, `_money_range`, `_upgrade_count`) slepiami nuo išorės.

**Žodžiais: kur kode naudojami keturi stulpai ir ką jie čia reiškia.** Visi keturi principai susiję su **ta pačia sritimi** — po lenktynių **chest** (dėžės) logika faile `f1_game/oop_rewards.py` ir jos iškvietimu iš `import pygame.py` (`DEFAULT_CHEST_REWARD_SERVICE.build_reward`). Žaidimo ciklas tik perduoda **finišo vietą**; sprendimai, kokio tier dėžė ir koks prizas, priklauso nuo OOP struktūros žemiau.

1. **Abstrakcija** — žodžiais: neįrašome visos išminties į vieną milžinišką funkciją. Vietoj to iškeliame **bendrą „piešinį“**: klasė `ChestTierRule` sako, kad *kiekviena* dėžės rūšis turi gebėti atsakyti, ar jai tinka pozicija, ir kaip išsukti prizą; *kas konkrečiai* — sidabras, auksas ir t. t. — lieka atskiroms klasėms. Taip atskiriame **bendrą idėją** nuo **konkretaus varianto**.

2. **Paveldėjimas** — žodžiais: sidabrinė, auksinė ir kitos taisyklės **nesukurtos nuo nulio kaip visiškai nepriklausomos** klasės. Jos **išplečia** tą patį karkasą (`ChestTierRule`), todėl bendras elgesys (pvz. kaip formuojamas `ChestReward`) gyvena vienoje vietoje, o skirtumai — pinigų intervalai, tier vardas, upgrade skaičius — uždaromi kiekvienoje dukterinėje klasėje be pasikartojančio kodo.

3. **Polimorfizmas** — žodžiais: servisas ir kitas kodas dirba su nuoroda į **bendrą tipą** (`ChestTierRule`) ir kviečia tuos pačius metodus (`roll_reward` ir pan.). **Kuris konkretus objektas** po gaubtu — sidabras ar deimantas — nusprendžiama vykdymo metu; to paties `build_reward` kūno pakanka visiems variantams, nes kiekviena klasė **pati žino**, kaip elgtis pagal kontraktą.

4. **Enkapsuliacija** — žodžiais: pinigų ribos, vidinis tier pavadinimas ir panašūs laukai laikomi **objekto viduje** (dažnai su pabraukimu `_` — signalas, kad tai implementacijos detalė). Išorė kreipiasi per viešus metodus, o ne keičia laukus ranka. Papildomas pavyzdys ekrane — `LEDDrop`: lašas **pats** saugo padėtį, greitį ir piešimą; piešimo ciklas tik kviečia `fall` / `draw`, neužkrauna visos logikos į vieną procedūrą.

```16:41:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/f1_game/oop_rewards.py
class ChestTierRule(ABC):
    """
    Abstract reward rule for a single chest tier.
    - Abstraction: abstract matches() contract.
    - Encapsulation: tier/money range/upgrade count are hidden internals.
    """

    def __init__(
        self, tier: str, money_range: Tuple[int, int], upgrade_count: int
    ) -> None:
        self._tier = tier
        self._money_range = money_range
        self._upgrade_count = upgrade_count

    @abstractmethod
    def matches(self, player_position: int) -> bool:
        """Return True if this rule should be used for position."""

    def roll_reward(
        self, upgrade_pool: Sequence[str], rng: random.Random = random
    ) -> ChestReward:
        cash = rng.randint(self._money_range[0], self._money_range[1])
        pool = list(upgrade_pool)
        rng.shuffle(pool)
        picks = pool[: min(self._upgrade_count, len(pool))]
        return ChestReward(tier=self._tier, cash=cash, upgrades=picks)
```

Papildomas **enkapsuliacijos** pavyzdys UI kontekste (lietus): klasė `LEDDrop` faile `import pygame.py` jungia būseną ir elgseną (`reset`, `fall`, `draw`).

```125:139:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/import pygame.py
class LEDDrop:
    def __init__(self):
        self.reset()
        self.y = random.randint(0, HEIGHT)
    def reset(self):
        self.x, self.y = random.randint(0, WIDTH), random.randint(-500, -50)
        self.speed = random.uniform(4, 9)
        self.width, self.length = random.randint(3, 5), random.randint(20, 60)
    def fall(self):
        self.y += self.speed
        if self.y > HEIGHT: self.reset()
    def draw(self, color):
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.length))

rain_drops = [LEDDrop() for _ in range(150)]
```

**Prijungimas prie žaidimo:** post-race chest vis dar kviečiamas iš pagrindinio failo, bet apdorojimas deleguotas į servisą.

```3049:3068:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/import pygame.py
def _apply_post_race_chest_rewards():
    """Po varžybų duoda chest su progresuojančiais prizais: pinigai + upgrade tokenai."""
    global post_race_chest, money_balance
    if post_race_chest is not None:
        return
    player_pos = 20
    if race_post_results_rows:
        for row in race_post_results_rows:
            c = race_session_cars[row["idx"]]
            if c.get("is_player"):
                player_pos = int(row["pos"])
                break
    reward = DEFAULT_CHEST_REWARD_SERVICE.build_reward(
        player_position=player_pos,
        upgrade_pool=UPGRADE_POOL,
        upgrade_inventory=upgrade_inventory,
        rng=random,
    )
    money_balance += reward.cash
    post_race_chest = {"tier": reward.tier, "cash": reward.cash, "upgrades": reward.upgrades}
```

---

### 2.2 Dizaino šablonas (bent vienas iš sąrašo)

**Pasirinktas šablonas:** **Factory Method** (`ChestRuleFactory` → `PositionChestRuleFactory`).

**Kodėl tinka:** chest tier priklauso nuo **diskretaus** žaidėjo finišo vietos intervalo; factory centralizuoja sprendimą „kurią taisyklę sukurti“, vietoj ilgos `if/elif` grandinės pagrindiniame cikle.

**Žodinis paaiškinimas, kur naudojamas šablonas.** **Factory Method** čia reiškia: yra klasė `PositionChestRuleFactory`, kuri atlieka **gamyklos** vaidmenį: jos **vienintelė aiški užduotis** — pagal finišo vietą **sukurti tinkamą** `ChestTierRule` objektą (t. y. tos vietos atitinkančios konkrečios klasės **egzempliorių**). `ChestRewardService` toliau elgiasi paprastai: jis **nebesprendžia** „kurį konkretų klasės vardą rašyti“, o klausia gamyklos: „duok taisyklę šiai pozicijai“, tada kviečia `roll_reward`. Taip **atskiriame** *sprendimą, kokį objektą instancijuoti*, nuo *to, kaip tas objektas skaičiuoja prizą* (tai lieka OOP taisyklėse). Šablonas **matomas kode** ten, kur yra abstrakti `ChestRuleFactory` su `create_rule` ir konkreti `PositionChestRuleFactory`, o `build_reward` naudoja `self._factory.create_rule(...)`.

```76:119:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/f1_game/oop_rewards.py
class ChestRuleFactory(ABC):
    """Factory Method pattern: chooses which concrete chest rule to create."""

    @abstractmethod
    def create_rule(self, player_position: int) -> ChestTierRule:
        """Return concrete rule object for given final position."""


class PositionChestRuleFactory(ChestRuleFactory):
    def create_rule(self, player_position: int) -> ChestTierRule:
        if player_position >= 16:
            return SilverChestRule()
        if player_position >= 11:
            return GoldenChestRule()
        if player_position >= 6:
            return EmeraldChestRule()
        return DiamondChestRule()


class ChestRewardService:
    ...
    def build_reward(
        self,
        player_position: int,
        upgrade_pool: Sequence[str],
        upgrade_inventory: Dict[str, int],
        rng: random.Random = random,
    ) -> ChestReward:
        # Primary path: explicit Factory Method pattern (listed requirement).
        primary_rule = self._factory.create_rule(player_position)
        reward = primary_rule.roll_reward(upgrade_pool, rng=rng)
        for upg in reward.upgrades:
            upgrade_inventory[upg] += 1
        return reward
```

**Kodėl ne Singleton čia:** singleton būtų prasmingas vienam globaliam „GameManager“, bet chest logikai svarbiau **objektų kūrimo lankstumas** pagal vietą — todėl **Factory Method** parinktas kaip tiesiogiai atitinkantis domeną.

---

### 2.3 Kompozicija ir / ar agregacija

**Vieta:** `f1_game/persistence.py`

- **Kompozicija:** `CareerSnapshot` sudarytas iš kelių domeninių objektų (`DriverIdentity`, `EconomyState`, …).
- **Agregacija:** `CareerDataManager` laiko nuorodą į `SnapshotSerializer` (priklausomybė įšvirkšta per konstruktorių), o ne paveldi visą serializavimo implementaciją.

```43:98:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/f1_game/persistence.py
@dataclass
class CareerSnapshot:
    """
    Composition example:
    CareerSnapshot is composed of multiple domain objects.
    """

    driver: DriverIdentity
    economy: EconomyState
    car_development: CarDevelopmentState
    meta: CareerMetaState
...
class CareerDataManager:
    """
    Aggregation example:
    manager aggregates serializer dependency via constructor injection.
    """

    def __init__(self, serializer: SnapshotSerializer) -> None:
        self._serializer = serializer

    def save_snapshot(self, file_path: str, snapshot: CareerSnapshot) -> None:
        self._serializer.save(file_path, snapshot)

    def load_snapshot(self, file_path: str) -> Optional[CareerSnapshot]:
        return self._serializer.load(file_path)
```

**Prijungimas:** `build_career_snapshot()` ir `apply_career_snapshot()` faile `import pygame.py` surenka / pritaiko globalius kintamuosius be žaidimo taisyklių keitimo.

```3641:3668:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/import pygame.py
def build_career_snapshot():
    return CareerSnapshot(
        driver=DriverIdentity(
            name=driver_data.get("Name", {}).get("text", ""),
            surname=driver_data.get("Surname", {}).get("text", ""),
            number=driver_data.get("Number", {}).get("text", ""),
            country=driver_data.get("Country", {}).get("text", ""),
        ),
        economy=EconomyState(
            money_balance=int(money_balance),
            upgrade_inventory=dict(upgrade_inventory),
            upgrade_levels=dict(upgrade_levels),
        ),
        car_development=CarDevelopmentState(
            car_part_tiers=dict(car_part_tiers),
            teammate_car_tiers=dict(teammate_car_tiers),
        ),
        meta=CareerMetaState(
            winning_team_name=winning_team_name,
            teammate_result=teammate_result,
            season_gp_index=int(season_gp_index),
            championship_points=_serialize_championship_points(),
            career_profile_unlocked=bool(career_profile_unlocked),
            season_started_once=bool(season_started_once),
            signing_bonus_given=bool(signing_bonus_given),
            selected_offer_name=selected_offer_name,
        ),
    )
```

---

### 2.4 Duomenų išsaugojimas: skaitymas ir rašymas į failą

**Formatas:** **JSON** (`saves/career_progress.json`).  
**Rašymas / skaitymas:** `JsonSnapshotSerializer` + `save_career_state_to_file` / `load_career_state_from_file`.

```66:82:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/f1_game/persistence.py
class JsonSnapshotSerializer(SnapshotSerializer):
    def save(self, file_path: str, snapshot: CareerSnapshot) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(asdict(snapshot), fh, ensure_ascii=False, indent=2)

    def load(self, file_path: str) -> Optional[CareerSnapshot]:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return CareerSnapshot(
            driver=DriverIdentity(**raw.get("driver", {})),
            economy=EconomyState(**raw.get("economy", {})),
            car_development=CarDevelopmentState(**raw.get("car_development", {})),
            meta=CareerMetaState(**raw.get("meta", {})),
        )
```

**Integracija į žaidimą:** paleidus programą — automatinis bandymas įkelti; klavišai **F5** / **F9**.

```3617:3726:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/import pygame.py
SAVE_FILE_PATH = os.path.join(BASE_DIR, "saves", "career_progress.json")
career_data_manager = CareerDataManager(serializer=JsonSnapshotSerializer())
...
def save_career_state_to_file():
    try:
        career_data_manager.save_snapshot(SAVE_FILE_PATH, build_career_snapshot())
    except Exception:
        # Persistence must never break gameplay flow.
        pass


def load_career_state_from_file():
    try:
        snapshot = career_data_manager.load_snapshot(SAVE_FILE_PATH)
        if snapshot is not None:
            apply_career_snapshot(snapshot)
    except Exception:
        pass


load_career_state_from_file()
```

```3974:3977:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/import pygame.py
            elif event.key == pygame.K_F5:
                save_career_state_to_file()
            elif event.key == pygame.K_F9:
                load_career_state_from_file()
```

---

### 2.5 Unit testai (`unittest`)

**Vieta:** katalogas `tests/`, pvz. `tests/test_oop_rewards.py`, `tests/test_persistence.py`.

```18:44:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/tests/test_oop_rewards.py
class TestPositionChestRuleFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = PositionChestRuleFactory()

    def test_creates_silver_for_high_positions(self) -> None:
        for pos in (16, 19, 20):
            with self.subTest(pos=pos):
                rule = self.factory.create_rule(pos)
                self.assertIsInstance(rule, SilverChestRule)
    ...
    def test_creates_diamond_for_top_positions(self) -> None:
        for pos in (1, 3, 5):
            with self.subTest(pos=pos):
                rule = self.factory.create_rule(pos)
                self.assertIsInstance(rule, DiamondChestRule)
```

Testai apima **pagrindinę chest taisyklių logiką** ir **JSON round-trip** karjeros objektui (žr. `tests/test_persistence.py`).

---

### 2.6 PEP8 / kodo stilius

**Vieta:** `pyproject.toml` — įrankis **Ruff**, taikomas paketui `f1_game/` ir `tests/`. Monolitinis `import pygame.py` sąmoningai **išimtas** iš automatinio formatavimo (`exclude`), nes pilnas 4000+ eilučių perkėlimas į PEP8 be didelio refaktoriaus būtų rizikingas; stilius kontroliuojamas ten, kur kodas modulinis ir testuojamas.

```1:15:/Users/kajuszeynalov/Documents/Universitetas/Kursinis/pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py310"
exclude = ["import pygame.py"]

[tool.ruff.lint]
# PEP 8: E, W; papildomai F (pyflakes), I (isort)
select = ["E", "W", "F", "I"]
ignore = [
  "E501", # eilučių ilgį kartais paliekame, jei skaitoma geriau
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

### 2.7 Funkciniai reikalavimai (trumpai, kur ieškoti kode)

| Funkcija | Kur kode |
|----------|-----------|
| Kvalifikacija / lenktynės / rezultatai | `import pygame.py` (`qual_*`, `race_tick_frame`, `draw_race_*`) |
| Chest pagal vietą | `f1_game/oop_rewards.py` + `_apply_post_race_chest_rewards()` |
| Duomenys (komandos, vairuotojai) | `f1_game/driver_data.py`, `game_data.py` (perexportas) |
| Kalendorius / trasos šablonas | `f1_game/season_calendar.py`, `f1_game/track_seed_data.py` |

---

## 3. Rezultatai

- **Pavyko** sujungti pilną žaidimo ciklą (nuo titulo iki chest ir sezono tęsinio) viename Pygame projekte su aiškiais `game_state` perėjimais.
- **Refaktorių etapas** išskaidė duomenis ir testuojamas dalis į `f1_game/` bei `tests/`, sumažinant riziką keisti core logiką atskiruose PR žingsniuose.
- **Iššūkis** — balansas tarp AI greičio, padangų dėvėjimo ir žaidėjo patirties; chest ir pinigų sistema turi likti motyvuojanti, bet ne per dosni.
- **Iššūkis** — monolitinis `import pygame.py` vis dar laiko didžiąją dalį piešimo ir įvykių; PEP8 taikomas selektyviai (žr. 2.6).
- **Testavimas** — `unittest` dengia izoliuotą chest ir JSON persistencijos branduolį; tai leidžia saugiau keisti taisykles be rankinio regreso.

---

## 4. Išvados ir plėtra

### Išvados

Programa įgyvendina kursinio tikslą: **veikianti F1 tematikos demonstracija** su lenktynėmis, progresija ir dokumentuojamais architektūros sprendimais (OOP, Factory Method, kompozicija/agregacija, failų I/O, `unittest`, stiliaus gairės moduliniuose failuose). Kritinės vietos atsekamos per ištraukas šiame skyriuje.

### Kaip plėtoti toliau

1. Perkelti likusį `import pygame.py` į mažesnius modulius (`race`, `ui`, `audio`) ir laikyti vieną `GameState` objektą vietoj `global`.
2. Išplėsti JSON saugojimą (pvz. čempionato lentelė po kiekvieno GP, nustatymai).
3. Pridėti daugiau trasų arba GP specifinių geometrijų failų.
4. CI (GitHub Actions) su `unittest` + `ruff check` kiekviename push.

---

## 5. Šaltiniai ir dokumentacija

- [Pygame dokumentacija](https://www.pygame.org/docs/)
- [Python dokumentacija](https://docs.python.org/3/library/unittest.html)
- [PEP 8](https://peps.python.org/pep-0008/)
- [Ruff linter / formatter](https://docs.astral.sh/ruff/)
- [Design Patterns — Factory Method (refactoring.guru)](https://refactoring.guru/design-patterns/factory-method)

---

*Ataskaita atnaujinta pagal dabartinę projekto būseną (OOP, šablonas, kompozicija, JSON, testai, PEP8/Ruff).*
