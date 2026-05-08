# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

В моём прогоне Ex7 (session `sess_9717fc5e818e`) bridge закрылся с
`rounds=2, summary: structured confirmed in round 2`. То есть планировщик
правильно расщепил задачу: исследовательская часть осталась на loop half,
а решение «зафиксировать бронь по политике площадки» отправилось на
structured half — туда, где `ActionValidateBooking` детерминированно
проверяет `party_size ≤ 8` и `deposit_gbp ≤ 300`. Сигнал, по которому
`DefaultPlanner` принял такое решение, я нашёл в задаче для loop:
формулировки про «policy rules», «commit», «under deposit cap» — это
триггеры, которые в системном промпте планировщика мапятся на
`assigned_half: "structured"`.

Что меня здесь зацепило — это *advisory* характер решения. Планировщик
лишь рекомендует, кто должен исполнить subgoal. Если бы у меня
structured half не был подключён (как в `research_assistant` из недели 3),
такой subgoal ушёл бы в пустоту, и orchestrator упал бы по failure
mode #4 из лекций. Раунд 1 в моём прогоне был именно про это: loop
сначала отдал бронь с формально валидной, но недопустимой суммой
депозита — bridge через `build_reverse_task` вернул её обратно с
причиной, и только в раунде 2 после правок депозита structured
ответил `committed=True, BK-7D401E9E`.

Главный вывод для меня: prose-интерпретация LLM — ненадёжная точка
архитектуры. Правила нельзя оставлять в формулировках задач, их надо
кодировать в Python структурной половины (`validator.py`,
`ActionValidateBooking`), и тогда даже если планировщик ошибётся в
ассайнменте, бронь физически не сможет пройти валидацию с плохими
числами. Это та самая «defense in depth», про которую говорилось на
лекции по hybrid-агентам.

### Citation

- `sessions/sess_9717fc5e818e/logs/trace.jsonl` — события `planner.plan`,
  `bridge.round`
- `sessions/sess_9717fc5e818e/handoffs_audit/` — два forward-handoff'а
  (round 1: rejected, round 2: committed)
- `homework-pub-booking/rasa_project/actions/actions.py:ActionValidateBooking`

---

## Q2 — Dataflow integrity catch

### Your answer

В моём финальном прогоне Ex5 (session `sess_156e7d642925`) integrity
check вернул `dataflow OK: verified 4 fact(s) against tool outputs` —
проверены `cloudy`, `12` (°C), `£540`, `£0`. Чтобы не описывать
«sucess scenario» вхолостую, я отдельно посадил себе шумную проверку
во время отладки: руками отредактировал сгенерированный
`workspace/flyer.html`, заменил `£540` на `£9999` (как раз тот пример,
который рекомендуют в `README.md` курса) и перезапустил `verify_dataflow`
поверх изменённого файла.

Результат: `ok=False`, `unverified_facts=['9999']`,
`summary: dataflow FAIL: 1 unverified fact(s): ['9999']`. Самое
интересное здесь — почему именно эта проверка ловит то, что человек
скипает. `verify_dataflow` не проверяет «выглядит ли число
правдоподобно», она сравнивает с ground truth в `_TOOL_CALL_LOG`,
куда каждый из четырёх тулов положил свои `arguments` и `output`
через `record_tool_call`. То есть если значение никогда не
производилось ни одним из тулов — даже если оно «похоже» на
правильную цифру и формула сошлась бы — оно фабрикация.

Это прямой ответ на риск из лекций по агентным системам: LLM
генерирует *правдоподобные* числа, и человеческий ревью на правдо­подобность
их не отличает от настоящих. Единственный надёжный фильтр — сравнение
с журналом тулов. И ровно поэтому я во всех четырёх функциях зову
`record_tool_call(...)` *до* `return`, в обеих ветках — `success=True`
и `success=False`. Иначе попытка восстановления (например, плохая
дата в `get_weather`) выпала бы из трассы, и LLM мог бы потом
сослаться на «полученные» данные, которых на самом деле в логе нет.

### Citation

- `sessions/sess_156e7d642925/logs/trace.jsonl` — `dataflow_check_passed`
- `homework-pub-booking/starter/edinburgh_research/integrity.py:99`
  (`fact_appears_in_log`) — рекурсивный скан `output` и `arguments`
- `homework-pub-booking/README.md` — пример «£540 → £9999» как
  каноничный negative-test

---

## Q3 — Removing one framework primitive

### Your answer

Если бы пришлось убрать одно из пяти архитектурных решений
sovereign-agent и пересобрать всё остальное, я бы оставил
**session directories** последним, что нельзя трогать. Они — мой
git-коммит этого фреймворка: можно вытащить из них что угодно, а
из всего остального — нельзя.

Аргумент в обратную сторону. Forward-only state machine (Decision 2)
важна, но сама по себе бесполезна без места, где хранятся переходы —
а это `session.directory`. Tickets (Decision 3) я могу пересобрать
как `.jsonl` внутри `session/tickets/` и не потерять контракт.
Atomic-rename IPC (Decision 5) полностью заменяемо опросом
`session/ipc_input/` с `os.rename` — медленнее, но семантика та же.
Tool registry (Decision 4) — самая «алгоритмическая» из пяти, и
её код помещается в один файл; перепишу за вечер, как я
переписал `build_tool_registry` для Ex5.

А теперь что будет, если убрать session directories. Во-первых —
изоляция: сейчас `Session.path()` физически режет escape наружу
(`SessionEscapeError`), без этого инкапсулирующего слоя чужие
сессии начинают видеть друг друга, потому что workspace’ы
сольются. Во-вторых — отладка превращается в SQL-археологию:
сейчас на любой вопрос «как эта бронь докатилась до коммита» я
делаю `cd sessions/sess_9717fc5e818e && cat handoffs_audit/*` и
вижу все три раунда; без директорий это ивенты, размазанные по
центральному логу с курсорной навигацией. В-третьих — integrity check
из Ex5 рассыпается: `_TOOL_CALL_LOG` живёт в памяти процесса, но
*workspace* для флаера — на диске сессии, и весь смысл проверки
«факт из файла = запись в логе» держится на том, что процессы
сессии видят один и тот же путь.

То есть session directories — это commit hash для всего остального.
Из коммита можно восстановить diff, blame, merge; из остального —
коммит нельзя. Поэтому, если жертвовать, я жертвую atomic-rename IPC
(Decision 5) — паттерн «директория-индикатор + polling» отлично
обходится без атомарности там, где достаточно eventual consistency.

### Citation

- `sessions/sess_156e7d642925/` — структура session-каталога,
  на которую опирается integrity check
- `sessions/sess_9717fc5e818e/handoffs_audit/` — пример того, как
  директория делает round-trip отлаживаемым
- `homework-pub-booking/starter/edinburgh_research/tools.py:285`
  — `session.workspace_dir` как точка записи флаера
