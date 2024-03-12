## ZOLLAMA-GPT

### General Overview

```mermaid
%%{init: {'theme': 'base', "loglevel":1,'themeVariables': {'lineColor': 'Blue', 'fontSize':'40px',"fontFamily": "Trebuchet MS"}}}%%
flowchart TD
    style PV fill:#fff
    style ZZ fill:#a7e0f2,stroke:#13821a,stroke-width:4px
    style LocalEnv fill:#a7e0f2
    style PSQL fill:#aaa
    style EMRADT fill:#a7e0f2
    style BI fill:#ffa,stroke:#13821a,stroke-width:8px
    style RM fill:#ffa,stroke:#13821a,stroke-width:8px

    classDef subgraph_padding fill:none,stroke:none
    EMRADT["POLL&nbspADT/EMR&nbspData"]
    ZZ(("`**ZOllama
    &nbsp&nbsp&nbsp&nbspService&nbspAPI**`"&nbsp&nbsp&nbsp))


    EMRADT ==> PV ====> ZZ ===> PVO
    PVO ====> OLLAMA
    Med ===> PPD ==Un-Encrypted=====> PSQL
    Med ==> EPPD ==Encrypted=====> PSQL
    Summary ===> Med
    BI <=====> PSQL
    RM <=====> PSQL

    subgraph PV["Patient&nbspVitals"]
        subgraph blank2[ ]
            PVN("Doctor Patient
            Visit Note
            (OSCE format)")
            PI["Patient ID"]
        end
    end

    subgraph LocalEnv["`**Local&nbspEnvironment**`"&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp]
        subgraph blank[ ]
            direction TB
            PSQL[("`**PostgreSQL**`")]
            subgraph BI["BI
            Workflows"]
            end
            subgraph RM["RCM
            Workflows"]
            end
            subgraph PVO["Original&nbspPatient&nbspNote"]
                direction LR
                subgraph blank3[ ]
                    direction LR
                    ORP("Doctor Patient
                        Visit Note
                        (OSCE format)")
                    ORPI["Patient ID"]
                end
            end
            subgraph OLLAMA["OLLAMA"]
                subgraph blank4[ ]
                    direction TB
                    subgraph Summary["Summarize Notes"]
                        subgraph blank7[ ]
                            LLM0[deepseek-llm]
                        end
                    end
                    subgraph Med["Medical"]
                        subgraph blank8[ ]
                            LLM1[medllama2]
                            LLM2[meditron]
                        end
                    end
                end
            end
            subgraph EPPD["Processed&nbspPatient&nbspData"]
                direction TB
                subgraph blank5[ ]
                    subgraph JSON
                        subgraph blank6[ ]
                            JAA["GPT Response: Summarized Note"]
                            JAB["GPT Response: Recommended Diagnoses"]
                        end
                    end
                end
            end
            subgraph PPD["Processed&nbspPatient&nbspData"]
                direction TB
                subgraph blank9[ ]
                    subgraph AJSON["JSON"]
                        subgraph blank10[ ]
                            JAC["GPT Response: Recommended Diagnoses ICD-10 codes"]
                            JAD["GPT Response: Recommended Diagnoses CPT codes"]
                            JAE["GPT Response: Recommended Prescription"]
                            JAF["GPT Response: Recommended Prescription CPT codes"]
                            JAG["GPT Response: Keywords"]
                        end
                    end
                end
                subgraph RDBMS
                    subgraph blank11[ ]
                    PID["Patient ID"]
                    end
                end
            end

            
        end
    end
    class blank subgraph_padding
    class blank2 subgraph_padding
    class blank3 subgraph_padding
    class blank4 subgraph_padding
    class blank5 subgraph_padding
    class blank6 subgraph_padding
    class blank7 subgraph_padding
    class blank8 subgraph_padding
    class blank9 subgraph_padding
    class blank9 subgraph_padding
    class blank10 subgraph_padding
    class blank11 subgraph_padding
```

#### API Overview
```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'lineColor': 'Blue'}}}%%
graph LR
    sub["/login"] --> sub1
    sub["/analyze_visit_note"] --> sub2
    sub["/analyze_visit_notes"] --> sub3
    sub["CLIENT"] --> sub0
    sub0["GET: Login"]
    sub1["POST: Generate JWT"]
    sub2["GET: Analyze Visit OSCE format Visit Note"]
    sub3["GET: Analyze all OSCE format Visit Notes that exist in database"]
```


**From ADT Feeds and/or EMR**: 
 * Captures medical conversations in Objective Structured Clinical Examinations (OSCE) format.
 * Condenses the medical conversation into a concise prompt.
 * Utilizes medllama LLMs to analyze the condensed conversation.
   - Converts the summarized note into a diagnosis and treatment plan.
   - Derives a prescription note based on the diagnosis and treatment plan.
   - Extracts ICD-10 codes from the diagnosis.
   - Adds details of ICD-10 codes by performing a lookup.
   - Extracts CPT codes from both diagnosis and prescription notes.
   - Retrieves details of CPT codes, such as description and billability.
   - Identifies keywords from the diagnosis and treatment plan.
   - Stores all information as various JSON documents in PostgreSQL.
 * Encrypts the analyzed text and incorporates it into a searchable JSON document in PostgreSQL.
  
**Deployed as WSGI**  
*  Uses Gunicorn WSGI

#### How-to Run
* Install Python Modules:
    > pip3 install -r requirements.txt

* Gen SSL key/cert for secure connection to the service
    > openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3650

* Gen Symmetric encryption key for encrypting any text
   > ./tools/generate_keys.py
   > Encrption Key File text_encryption.key created

* Create Database and tables:
    See **zollama.sql**

### Install Ollama-gpt 

#### Linux
* https://github.com/ollama/ollama/blob/main/docs/linux.md

* Sample Debian Service config file: /etc/systemd/system/ollama.service
Add **OLLAMA_HOST** environment variable to allow remote access
```shell
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
..
..
..

```

#### MacOS
* I installed Ollama-gpt on my MacMini M1 - using brew
```shell
> brew install ollama
```
* Start/Stop Service
```shell
> brew services start ollama
> brew services stop ollama
```

**Bind Ollama server to local IPV4 address**

* create a run shell script
  ```shell
  > /opt/homebrew/opt/ollama/bin
  ```
* Create a script named **ollama.sh** add the following
  ```shell
  #!/usr/bin/env bash
  export OLLAMA_HOST=0.0.0.0
  /opt/homebrew/bin/ollama $1
  ```
* Make script "executable"
  ```shell
  chmod +x ollama.sh
  ```
* Edit .plist file for the ollama homebrew service
  ```shell
    > cd /opt/homebrew/Cellar/ollama
    > cd 0.1.24 #this may be different for your system
    > vi homebrew.mxcl.ollama.plist
  ```
* Change original line
  > <string>/opt/homebrew/opt/ollama/bin/ollama</string>

    TO this:
  > <string>/opt/homebrew/opt/ollama/bin/ollama.sh</string>
* Save file
* stop/start service
  ```shell
  > brew services stop ollama && brew services start ollama
  ```
* Add following models to ollama-gpt: deepseek-llm,llama2,llama-pro 
  ```shell
  > for llm in deepseek-llm llama2 llama-pro gemma
    do
        ollama pull ${llm}
    done
  ```
* Update setup.config with pertinent information (see setup.config.template)
  ```text
     # update with required information and save it as
     #	setup.config file
    [psqldb]
    host=
    port=5432
    database=
    user=
    password=

    [service]
    JWT_SECRET_KEY=
    SRVC_SHARED_SECRET=
    IDENTITY=
    APP_SECRET_KEY=
    ENDPOINT_URL=
    OLLAMA_API_URL=
    LLMS=
    MEDLLMS=
    ENCRYPTION_KEY=
  ```

* Run Zollama-GPT Service:
    (see https://docs.gunicorn.org/en/stable/settings.html for config details)
```shell
    > gunicorn --certfile=cert.pem \
               --keyfile=key.pem \
               --bind 0.0.0.0:5000 \
               zollama:app \
               --timeout 2592000 \
               --threads 4 \
               --reload
```

**Seed the DB with Anonymized Read World OSCE Notes**
> ./seed_data.py
 
**Script Output**
```shell
MedData/Clean Transcripts/RES0181.txt
MedData/Clean Transcripts/RES0195.txt
MedData/Clean Transcripts/GAS0001.txt
```
* Customize it to your hearts content!

* **LICENSE**: The 3-Clause BSD License - license.txt

* **TODO**:
    - Add Swagger Docs
    - Add long running task queue
        - Queue: task_id, task_status, end_point
    - Revisit Endpoint logic add robust error handling
    - Add logic to handle list of lists with NUM_ELEMENTS_CHUNK elements
        - retry after 429
        - break down longer list of items into list of lists with small
            chunks

#### How-to use the API examples
* These examples assume that environment variable **API_KEY** is using a valid API_KEY


**Chat Prompt a given visit note id**
```shell
> export api_key=<api_key>
>
> export AT=$(curl -sk -X POST -H "Content-Type: application/json" -d '{"api_key":"'${foo}'"}' \
https://127.0.0.1:5001/login | jq -r .access_token) \
&& curl -sk -X GET -H "Authorization: Bearer ${AT}" 'https://127.0.0.1:5001/analyze_visit_note?visit_note_id=<visit note id>'
```

**Chat Prompt ALL patient visit notes that are currently stored in  database**
```shell
> export api_key=<api_key>
>
> export AT=$(curl -sk -X POST -H "Content-Type: application/json" -d '{"api_key":"'${foo}'"}' \
https://127.0.0.1:5001/login | jq -r .access_token) \
&& curl -sk -X GET -H "Authorization: Bearer ${AT}" 'https://127.0.0.1:5001/analyze_visit_notes'
```


#### Database Schema
![Database Schema](database.png)

#### llama-gpt VM config 

*nVidia GTX-1070i 8GB in Passthrough Mode*

![llama-gpt-vm](llama-gpt-vm.png)


#### PostgreSQL VM config
![postgresql-vm](postgresql-vm.png)
