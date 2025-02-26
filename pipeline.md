```mermaid
sequenceDiagram
    participant C as Client
    participant S as Service
    participant D as Database
    C->>S: POST server_com/create_pipeline
    S->>D: insert pipeline
    S->>D: insert stage_1
    S->>D: ...
    S->>D: insert stage_n
    D->>S: Success or Error
    S->>C: Success or Error
```

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Service
    participant D as Database
    C->>S: POST server_com/start_pipeline "name: pipeline"
    S->>D: insert job_status with stage=1 and status=in process
    D->>S: Start job_id or Error
    S->>C: Start job_id or Error on start
    Note right of S: Execute stages
    S->>D: update stage in job_id
    S->>D: if all stages have done set status=ended successfully<br/>else set status=ended with error
    S->>C: Successfully completed<br/> or ended with error on stage_i
```

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Service
    participant D as Database
    C->>S: GET server_com/status_job?job_id=<идентификатор>
    S->>D: get stage_index_in_pipeline where job_id=<идентификатор>
    D->>S: stage_index_in_pipeline
    S->>C: stage_index_in_pipeline
```

Для создания pipeline отправляется HTTP POST-запрос на server.com/create_pipeline с данными в формате json следующего вида:
```json
{
    "pipeline_name": <имя pipeline>,
    "stages": <перечисление каждой стадии с их порядковыми номерами с описанием каждой из них в формате json>
}
```

Каждая стадия pipeline также описывается в формате json и имеют следующий вид:
```json
<порядковый номер стадии в конкретном pipeline>:
    {
        "stage_type": <тип сервиса, который вызывается данной стадией, например, http. Возможные варианты типов описаны ниже>,
        "stage_params": <параметры, передающиеся в стадию, в формате json>
    }
```

В качестве параметров стадии могут выступать, например, параметры пути в HTTP запросе, передаваемые данные, возвращаемые значения, возможность передачи выходных параметров в следующую стадию и т.д.

По итогам создания pipeline сервер возвращает сообщение об успешном создании pipeline или ошибку, возникшую при его создании.

Для запуска pipeline отправляется HTTP POST-запрос на server.com/start_pipeline с заголовком вида "name: <имя pipeline>" и данными, необходимыми для работы сервиса. Сервер возвращает идентификатор начавшейся job.

Чтобы узнать текущую стадию job отправляется HTTP GET-запрос на server.com/status_job?job_id=<идентификатор>.

Структура базы данных, обслуживающей работу с pipeline представлена ниже:

```mermaid
erDiagram
    PIPELINES {
        int pipeline_id PK
        text pipeline_name "constraint UNIQUE and length < 50"
        int first_stage FK "references stages(stage_id)"
    }
    
    STAGES {
        int stage_id PK
        int pipeline_id FK "references pipelines(pipeline_id)"
        int next_stage FK "references stages(stage_id) or null if this is last stage of pipeline"
        int stage_index_in_pipeline
        text type "for example, http"
        json stage_params 
    }

    JOBS_STATUS {
        int job_status_id PK
        int pipeline_id FK "references pipelines(pipeline_id)"
        int stage_id FK "references stages(stage_id)"
        text job_status "in process/ended succesfully/ended with error"
        text job_error "code of error with description or null"
    }

    PIPELINES ||--|{ STAGES : first_stage
    STAGES ||--|| STAGES : next_stage
    JOBS_STATUS }|--|| STAGES : stage_id
    JOBS_STATUS }|--|| PIPELINES : pipeline_id
    
```
В качестве примера работы с данным сервисом приведем пример pipeline, позволяющий создать пользователя в базе данных, а затем получнием jwt для дальнейшей авторизации:

Сначала создадим описанный pipeline. Для этого отправляем HTTP POST-запрос на server.com/create_pipeline с данными:
```json
{
    "pipeline_name": "Authorization",
    "stages": 
        {
            "1":
                {
                    "stage_type": "HTTP",
                    "stage_params": 
                        {
                            "url_path": "server.com/users",
                            "data": ["login", "password"],
                            "return_value": "user_id",
                            "return_codes": [200, 400],
                            "transfer_return_value_to_next_stage": true
                        }
                },
            "2":
                {
                    "stage_type": "HTTP",
                    "stage_params": 
                        {
                            "url_path": "server.com/auth",
                            "data": "user_id",
                            "return_value": "jwt",
                            "return_codes": [200, 400]
                        }
                }
        }
}
```

Для запуска данного pipeline необходимо отправить HTTP POST-запрос на server.com/start_pipeline с заголовком "name: Authorization" с данными "login: user, password: 123".
