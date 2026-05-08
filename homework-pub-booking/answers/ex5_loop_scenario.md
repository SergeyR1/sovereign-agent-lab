# Ex5 — Edinburgh research loop scenario

## Your answer

В моём прогоне (session `sess_156e7d642925`, FakeLLMClient) планировщик
разложил задачу на два подцели: `sg_1` — собрать данные по площадкам,
погоде и стоимости в районе Haymarket, и `sg_2` — оформить HTML-флаер
по результатам. Эту декомпозицию видно по тикетам в логе:
`tk_4cdb51af planner.plan`, `tk_50cf21bb executor.run_subgoal/sg_1`,
`tk_1912570d executor.run_subgoal/sg_2` — все три закрылись со
статусом `success`.

В `sg_1` исполнитель отправил три read-only вызова — `venue_search`,
`get_weather`, `calculate_cost` — параллельной пачкой; так и должно
быть, потому что все три зарегистрированы с `parallel_safe=True`
(чистое чтение фикстур и арифметика, общего состояния они не трогают).
В `sg_2` пошёл `generate_flyer`, и он специально сериализован
(`parallel_safe=False`), потому что пишет файл в `session.workspace_dir`
— это write-operation, и пускать её в параллель с другими записями
нельзя без риска гонки.

Каждая из четырёх функций перед `return` вызывает
`record_tool_call(name, arguments, output)` из `integrity.py`. На этом
держится весь dataflow check: `verify_dataflow` проходит по тексту
флаера, выдёргивает регулярками денежные суммы, температуры и
погодные ярлыки, а потом для каждого факта спрашивает у
`fact_appears_in_log`, видела ли его уже какая-то запись в
`_TOOL_CALL_LOG` — в `output` или в `arguments`. У меня итог чистый:
`dataflow OK: verified 4 fact(s) against tool outputs` —
проверены `cloudy`, `12` (°C), `£540`, `£0`. Если бы я где-то в
HTML вписал, например, `£9999`, которого никогда не было в выводах
тулов, integrity-check вернул бы `ok=False` с этим числом в
`unverified_facts` — ровно тот сценарий, который тестирует
`test_verify_dataflow_catches_obvious_fabrication`.

Для устойчивости тулов я разделил два режима ошибок: отсутствие
fixture-файла или его повреждение даёт `raise ToolError(SA_TOOL_DEPENDENCY_MISSING)`
(это конфигурационная проблема, исполнителю стоит упасть), а
неизвестный город/дата/площадка/тариф — это `success=False` с
`SA_TOOL_INVALID_INPUT` без исключения, чтобы LLM мог получить
сообщение и поправить аргументы. И в обеих ветках я всё равно зову
`record_tool_call` до возврата, иначе попытка восстановления потерялась бы из трассы.
