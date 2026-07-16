---

title: INPAC-Cluster-Operational-Guide

type: note

permalink: hephaestus/knowledge-base/core/inpac-cluster-operational-guide

---



# INPAC Cluster Operational Guide



This document contains the essential protocols and configuration details for interacting with the INPAC computing cluster. All AI agents MUST adhere to these guidelines.



---



## 1. Connection Protocol



- **Entry Point:** All SSH connections must be made to the login node.

  - **Address:** `bl-0.inpac.sjtu.edu.cn`



## 2. Filesystem Strategy



The cluster has multiple filesystems. To ensure performance and data integrity, the following usage protocol is mandatory:



- **Code & Workspace (`/lustre`):**

  - **Path:** `/lustre/your_group/your_user_name/`

  - **Purpose:** This is the primary working directory. Its high-performance I/O is ideal for deploying our Git repository, running compilations, and storing simulation output.

  - **CRITICAL NOTE:** This filesystem is **NOT backed up**. Version control via Git is our only safety net.



- **Home Directory (`/home`):**

  - **Path:** `/home/your_user_name/`

  - **Purpose:** Limited use only. For storing persistent configuration files (e.g., `.bashrc`) or small scripts.

  - **Constraint:** Has a small quota (20 GB). **DO NOT** store code repositories or simulation data here.



- **Deprecated Filesystem (`/store/bl2`):**

  - **Status:** **PROHIBITED.** The hardware is aging. This filesystem must not be used for any operations.



## 3. Software Environment Protocol



The cluster's software is managed via modules and CVMFS. The correct environment **MUST** be sourced before any compilation or execution.



- **Primary Environment (LCG/CVMFS):** This is the preferred method as it provides a comprehensive, up-to-date suite of HEP software.

  - **Command:** `source /cvmfs/sft.cern.ch/lcg/views/LCG_98python3/x86_64-centos7-gcc9-opt/setup.sh`

  - **Usage:** This command **MUST** be run in any script before `cmake`, `make`, or executing the simulation/analysis programs. It provides Geant4, ROOT, Python 3, and a modern GCC compiler.



## 4. HTCondor Job Submission Protocol



All large-scale computations MUST be submitted to the HTCondor batch system.



- **Submission Command:** `condor_submit <job_file.sub>`



- **Standard Job File Template (`job.sub`):**

  ```sub

  Universe   = vanilla

  Executable = /path/to/your/executable/or/script.sh



  # --- Arguments for the executable ---

  Arguments  = --input-file data.mac --output-file results.root



  # --- Logging ---

  Log        = logs/job_$(ClusterId).log

  Output     = logs/job_$(ClusterId).out

  Error      = logs/job_$(ClusterId).err



  # --- Resource Request ---

  # For multi-threaded applications (like 'make -jN'), request N CPUs.

  request_cpus = 8

  

  # --- CRITICAL: Filesystem Configuration ---

  # INPAC has a shared filesystem. DO NOT transfer files.

  should_transfer_files = NO



  # --- Asynchronous Post-Processing & Callback ---

  # This command runs automatically on the worker node AFTER the main job succeeds.

  # It is the designated mechanism for our workflow's callback trigger.

  +PostCmd = "/path/to/your/analysis/scripts/post_process.py"

  +PostArguments = "--job-id $(ClusterId) --status success"



  Queue

  ```



- **GPU Jobs:** For future ML tasks, GPU nodes can be requested by adding:

  ```sub

  request_GPUs = 1

  # Specify GPU model if needed, e.g., V100 or A100

  +SJTU_GPUModel = "A100_80G"

  ```


