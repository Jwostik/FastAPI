```mermaid
erDiagram
    JOBS {
        int job_id PK
        text job_name UNIQUE "constraint length < 50"
        int first_stage FK "references stages(stage_id)"
    }
    
    STAGES {
        int stage_id PK
        int next_stage "references stages(stage_id) or null if this is last stage of job"
        int stage_index_in_job
        text http_method "constraint POST or GET or ..."
        text http_path "constraint length < 50"
        response_status_codes allowed_response_status_codes "CREATE TYPE response_status_codes AS ENUM (200, 400);"
    }

    JOBS_STATUS {
        int job_status_id PK
        int job_id FK "references jobs(job_id)"
        int stage_id FK "references stages(stage_id)"
    }
    
```
