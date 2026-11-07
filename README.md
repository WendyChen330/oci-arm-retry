# OCI Free VM Retry Script | OCI 免費 VM 搶機腳本

Automated retry scripts to claim Oracle Cloud Always Free VMs (ARM A1.Flex / x86 E2.1.Micro) via GitHub Actions — no need to keep your computer on 24/7.

🌐 [English](#english) | [繁體中文](#繁體中文)

---

<a name="english"></a>
# English

## Two Scripts

| Script | Instance Type | Spec | Architecture |
|--------|--------------|------|--------------|
| `oci_retry.py` | VM.Standard.A1.Flex | 2 OCPU / 12 GB RAM / 100 GB disk | ARM (Ampere) |
| `oci_retry_micro.py` | VM.Standard.E2.1.Micro | 1/8 OCPU / 1 GB RAM / 50 GB disk | x86 |

Both shapes are part of the Oracle Always Free tier. Always Free instances and volumes must be created in your tenancy's **home region**. The free allowance is:

- **Ampere A1:** 2 OCPUs + 12 GB RAM in total per tenancy
- **Micro:** up to 2 instances (1/8 OCPU each, can burst higher)
- **Storage:** 200 GB of boot + block volumes in total

> 📌 **Always Free update (June 15, 2026):** Oracle's official Always Free page lowered the Ampere A1 allowance from 4 OCPUs + 24 GB RAM to **2 OCPUs + 12 GB RAM** per tenancy.  
> Official source: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

---

## Two Ways to Run

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| Run locally | Quick testing | No GitHub setup needed | Your computer must stay on |
| GitHub Actions (recommended) | Long-term automated retrying | 24/7, no computer resources needed | Requires a **public** repo + Secrets setup |

> 💡 **Why public repo?** Public repositories get unlimited GitHub Actions minutes for free. Private repos have a monthly limit.

---

## Script Configuration

Open the script and edit the variables at the top:

> 💡 `COMPARTMENT_ID` can be left empty: the script then uses the `tenancy` value (your tenancy OCID) from the OCI config file. In GitHub Actions, that file is created from the `OCI_TENANCY` GitHub Secret; when running locally, it is your `~/.oci/config`. Fill it in only if you want to create the instance in a compartment other than your tenancy.
>
> The SSH public key is not set in the script: GitHub Actions reads the `OCI_SSH_PUBLIC_KEY` GitHub Secret (see Step 3 under Setup Steps), and local runs read the file set by `ssh_public_key_file` in your OCI config.

### ARM script: `oci_retry.py`

```python
COMPARTMENT_ID = ""  # Leave empty to use your tenancy (root compartment) from the OCI config
INSTANCE_NAME = "arm-server"
UBUNTU_VERSION = "24.04"  # OS for the new instance: "24.04" (default), "26.04" or "22.04"
ARM_OCPUS = 2
ARM_MEMORY_IN_GBS = 12
BOOT_VOLUME_SIZE_IN_GBS = 100
RETRY_INTERVAL = 90  # Retry interval in seconds
```

> `BOOT_VOLUME_SIZE_IN_GBS` sets the boot volume size. Always Free includes `200 GB` of boot + block volume storage in total; the ARM default of `100 GB` leaves room for two Micro instances (`50 GB` each). Lower `BOOT_VOLUME_SIZE_IN_GBS` if you also use other volumes.

### Micro script: `oci_retry_micro.py`

```python
COMPARTMENT_ID = ""  # Leave empty to use your tenancy (root compartment) from the OCI config
INSTANCE_NAME  = "micro-server"   # Change to "micro-server-2" when claiming your second Micro instance
UBUNTU_VERSION = "24.04"  # OS for the new instance: "24.04" (default), "26.04" or "22.04"
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # Retry interval in seconds
```

> Each OCI account can have up to **2 free Micro instances**. To claim a second one, change `INSTANCE_NAME` to a different value (e.g. `"micro-server-2"`) so both instances can be identified separately in the OCI Console. The VCN and subnet are shared between instances automatically.

> ⚠️ **Regions with multiple availability domains (ADs):** Oracle's [Always Free page](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) states that Micro instances "can only be created in one availability domain", but does not say which one. The scripts always use the **first** AD returned by the API (`ads[0]` in `get_availability_domain()`). If your region has several ADs and the Micro script never succeeds, check your Micro limit per AD in the OCI Console (search for **Limits, Quotas and Usage**), then change `ads[0]` to the index of that AD. Regions with a single AD (e.g. `ap-singapore-1`) are not affected.

### Ubuntu version (both scripts)

`UBUNTU_VERSION` sets which Ubuntu LTS is installed on the **new** instance. The script always picks the newest Oracle image build of that version. Changing it only affects instances created afterwards; instances you already have keep their OS.

| Version | Standard security updates until | Default Python |
|---------|-------------------------------|----------------|
| `"26.04"` | May 2031 | 3.14 |
| `"24.04"` (default) | May 2029 | 3.12 |
| `"22.04"` | May 2027 | 3.10 |

Sources: [Ubuntu release cycle](https://ubuntu.com/about/release-cycle), [python3-defaults](https://launchpad.net/ubuntu/+source/python3-defaults).

### Get Compartment ID (Tenancy OCID)

**Purpose**: Tells Oracle which account to create resources under. Only needed if you want a compartment other than your tenancy (root compartment); otherwise leave `COMPARTMENT_ID` empty.

1. Oracle Cloud Console → top-right **Profile** menu → **Tenancy: XXX**
2. Or: top-left menu → **Identity & Security** → **Identity** → **Compartments** → click root
3. Copy the OCID (format: `ocid1.tenancy.oc1..xxxxxx`)

### Get SSH Public Key

**Purpose**: Used to SSH into the instance after it's created.

1. When creating an instance in Oracle Cloud, choose **Generate key pair** (Generate SSH key pair)
2. Download two files:
   - `*.key` or `*.pem` (private key — keep this safe, used for SSH login)
   - `*.pub` (public key — GitHub Actions: add its contents as the `OCI_SSH_PUBLIC_KEY` GitHub Secret, see Step 3 under Setup Steps; local runs: set `ssh_public_key_file` in your OCI config to this file)
3. Open the `.pub` file in a text editor, copy all content (starts with `ssh-rsa AAAA...`)

Or generate your own key locally with `ssh-keygen`.

---

## Run Locally

### 1. Create the OCI Config File

**Location**: `~/.oci/config` (on Windows: `C:\Users\YourName\.oci\config`, no file extension)

```
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxxx
region=ap-singapore-1
key_file=C:\Users\YourName\Desktop\private-key.pem
ssh_public_key_file=C:\Users\YourName\Desktop\ssh-key.pub
```

**How to get config values**:
1. Oracle Cloud Console → top-right **Profile** menu → **User settings**
2. Left menu → **My profile** → top menu → **Tokens and keys** → **Add API key**
3. Choose **Generate API key pair** → download the private key (`.pem` file)
4. Click **Add** → copy the configuration snippet that appears, paste it into your `config` file
5. Update `key_file` to the actual path of your `.pem` file
6. Make sure `region` is your tenancy's **home region**, because Always Free resources can only be created there. To find it, click the region name at the top right of the Console; the menu shows your **Home region** (e.g. `Singapore (Singapore)`). Use its Region Identifier (e.g. `ap-singapore-1`) from Oracle's [region list](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)
7. Add `ssh_public_key_file` with the path to your SSH public key (`.pub`, see **Get SSH Public Key** above). The script installs this key on the new instance

### 2. Adjust Script Settings (Optional)

Instance name, Ubuntu version and the other settings are at the top of each script. See **Script Configuration** above.

### 3. Install and Run

```bash
# Install dependencies (once only)
pip install oci

# Run ARM version
python oci_retry.py

# Run Micro version
python oci_retry_micro.py
```

### Script Behavior

| Status | Description |
|--------|-------------|
| Initializing | Auto-creates VCN + subnet (skips if already exists) |
| Retry loop | Attempts every `RETRY_INTERVAL` seconds |
| Out of capacity | Prints ❌ and keeps retrying |
| Network timeout | Prints ⚠️ and keeps retrying (won't crash) |
| Other errors when creating the instance (e.g. limit reached) | Prints ❌ with the error message and keeps retrying — if it never succeeds, check the log |
| Setup errors (e.g. wrong OCID or API key) | Stops with an error before the retry loop starts |
| Success | Prints ✅ instance ID and stops automatically |

> **Open ports:** When the script creates a new VCN, it opens inbound TCP **22 (SSH), 80 (HTTP) and 443 (HTTPS)** from anywhere (`0.0.0.0/0`). An existing VCN is reused as-is. To open other ports, add them to the port list in `create_vcn_and_subnet()` before the first run, or add ingress rules to the VCN's security list in the OCI Console later. On OCI Ubuntu images, the port must also be allowed in the instance's `iptables` — see the "Update firewall settings" step in Oracle's [Apache on Ubuntu tutorial](https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/apache-on-ubuntu/01oci-ubuntu-apache-summary.htm).

---

## GitHub Actions — Automated 24/7 Retry (Recommended)

No need to keep your computer running. GitHub Actions retries continuously, 24 hours a day.

### How It Works

```
Job starts
  └─ Attempts every 90 seconds for ~330 minutes (~220 tries)
       ├─ Instance claimed → workflow auto-disables, done
       ├─ Script error (e.g. wrong secrets) → chain stops with an error message
       └─ Timeout → immediately triggers next Job (virtually no gap)
                        └─ Repeats...

If the chain breaks: manually go to the Actions tab and click Run workflow again
```

| Item | Details |
|------|---------|
| Duration per Job | ~330 minutes (~220 attempts) |
| Relay method | Auto-triggers next Job when the time limit is reached, virtually no gap |
| Max concurrency | 1 running + 1 queued (no pile-up) |
| On script error | Chain stops and shows an error; fix the problem, then click Run workflow again |
| If chain breaks | Manually trigger from Actions tab |
| After success | Workflow auto-disables; if that fails, the run shows an "Auto-disable failed" error and you disable it manually |
| ARM vs Micro | Separate workflows — **running only one at a time is recommended** |

> ⚠️ Both workflows use the same OCI account. Running ARM and Micro at the same time with the default `RETRY_INTERVAL` (90 seconds) causes OCI to return `TooManyRequests` errors. We recommend not starting both workflows at the same time.

---

## Setup Steps

### Step 1: Create a GitHub Repository

Create a **public** repository (public repos get unlimited Actions minutes).

### Step 2: Generate OCI API Key

1. Oracle Cloud Console → top-right **Profile** menu → **User settings**
2. Left menu → **My profile** → top menu → **Tokens and keys** → **Add API key**
3. Choose **Generate API key pair** → download the private key (`.pem` file)
4. Click **Add** → from the configuration snippet, note these values:
   - `user`, `fingerprint`, `tenancy`, `region`

### Step 3: Set GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

You need **6 secrets** in total:

| Secret Name | Value | Where to Get It |
|-------------|-------|----------------|
| `OCI_USER` | `ocid1.user.oc1..xxxxxx` | Oracle Console → My profile → OCID |
| `OCI_FINGERPRINT` | `xx:xx:xx:xx:xx` | Oracle Console → My profile → API keys → Fingerprint |
| `OCI_TENANCY` | `ocid1.tenancy.oc1..xxxxxx` | Oracle Console → top-right **Profile** menu → **Tenancy: &lt;name&gt;** → OCID |
| `OCI_REGION` | e.g. `ap-singapore-1` | Your **home region**: click the region name at the top right of the Oracle Console; the menu shows **Home region** (e.g. `Singapore (Singapore)`). Enter its Region Identifier (e.g. `ap-singapore-1`, see the [region list](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)). Always Free resources can only be created there |
| `OCI_PRIVATE_KEY` | Full contents of `.pem` file | Open the `.pem` from Step 2, copy everything (including `-----BEGIN/END PRIVATE KEY-----`) |
| `OCI_SSH_PUBLIC_KEY` | Full contents of your `.pub` file | See **Get SSH Public Key** above (starts with `ssh-`) |

> No GitHub token is needed: relaying to the next Job and auto-disabling use the workflow's built-in `GITHUB_TOKEN`, which GitHub creates for each Job automatically.

### Step 4: Push Code to GitHub

```bash
git remote add origin https://github.com/your-username/your-repo.git
git branch -M main
git push -u origin main
```

### Step 5: Start the Workflow

1. Go to your repository → **Actions** tab
2. If the workflow shows as disabled, click **Enable workflow**
3. Click **Run workflow** to trigger the first run manually

ARM and Micro have separate workflows. Running only one at a time is recommended (see the note under How It Works).

---

## After Success

Once an instance is claimed, the workflow **auto-disables**. If the run shows an **Auto-disable failed** error instead, disable it manually: Actions tab → the workflow → **...** → **Disable workflow**.

Go to Oracle Cloud Console → **Compute** → **Instances** → find your instance's public IP, then SSH in:

```bash
ssh -i private-key.pem ubuntu@your-public-ip
```

---

## Notes

- `COMPARTMENT_ID` in the script is safe to commit (non-sensitive)
- Sensitive values (OCI API private key) are stored in GitHub Secrets and never committed
- **Change on November 7, 2026:** the workflows no longer use a `GH_PAT` secret. If you forked or copied this repo before that date, replace your `.github/workflows/oci_retry.yml` and `.github/workflows/oci_retry_micro.yml` with the current versions from this repo (the scripts don't need to change; if you update the scripts as well, also add the `OCI_SSH_PUBLIC_KEY` GitHub Secret). After that, you can delete the `GH_PAT` secret and revoke the token in GitHub → Settings → Developer settings
- `.pem` / `.key` / `.pub` files are in `.gitignore` and won't be tracked

---
---

<a name="繁體中文"></a>
# 繁體中文

## 兩種腳本

| 腳本 | 目標機型 | 規格 | 架構 |
|------|---------|------|------|
| `oci_retry.py` | VM.Standard.A1.Flex | 2 OCPU / 12 GB RAM / 100 GB 磁碟 | ARM (Ampere) |
| `oci_retry_micro.py` | VM.Standard.E2.1.Micro | 1/8 OCPU / 1 GB RAM / 50 GB 磁碟 | x86 |

兩種機型都屬於 Oracle Always Free 永久免費方案。Always Free 的機器和磁碟都必須建立在帳號的**主區域（home region）**。免費額度如下：

- **Ampere A1：** 每個 tenancy 合計 2 OCPU + 12 GB RAM
- **Micro：** 最多 2 台（每台 1/8 OCPU，可短暫使用更多 CPU）
- **儲存空間：** boot volume + block volume 合計 200 GB

> 📌 **官方更新（2026-06-15 起）：** Oracle 官方 Always Free 頁面將 Ampere A1 額度從 4 OCPU + 24 GB RAM 調降為每個 tenancy **2 OCPU + 12 GB RAM**。  
> 官方來源：https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

---

## 兩種使用方式

| 方式 | 適合對象 | 優點 | 缺點 |
|------|---------|------|------|
| 本機執行 | 想快速試試 | 不需要 GitHub 帳號設定 | 電腦要一直開著 |
| GitHub Actions（推薦）| 長期自動搶機 | 24 小時不間斷，不佔電腦資源 | 需要 **public 倉庫** + 設定 Secrets |

> 💡 **為什麼需要 public 倉庫？** Public 倉庫可以免費使用無限制的 GitHub Actions 分鐘數。Private 倉庫每月有上限。

---

## 腳本設定

開啟腳本，修改最上方的變數：

> 💡 `COMPARTMENT_ID` 可以留空：腳本會自動使用 OCI 設定檔裡的 `tenancy`（你的租用戶 OCID）。在 GitHub Actions 上，這個設定檔是由 GitHub Secrets 的 `OCI_TENANCY` 產生；在本機執行時，就是你的 `~/.oci/config`。只有想把機器建在租用戶以外的區間（compartment）時才需要填。
>
> SSH 公開金鑰不在腳本裡設定：GitHub Actions 讀取 GitHub Secrets 的 `OCI_SSH_PUBLIC_KEY`（設定方式見「設定步驟」Step 3），本機執行則讀取 OCI 設定檔裡 `ssh_public_key_file` 指定的檔案。

### ARM 腳本：`oci_retry.py`

```python
COMPARTMENT_ID = ""  # 留空則使用 OCI 設定檔中的租用戶（根區間）
INSTANCE_NAME = "arm-server"
UBUNTU_VERSION = "24.04"  # 新機器安裝的作業系統："24.04"（預設）、"26.04" 或 "22.04"
ARM_OCPUS = 2
ARM_MEMORY_IN_GBS = 12
BOOT_VOLUME_SIZE_IN_GBS = 100
RETRY_INTERVAL = 90  # 重試間隔（秒）
```

> `BOOT_VOLUME_SIZE_IN_GBS` 是開機磁碟（boot volume）的大小。Always Free 的 boot volume + block volume 儲存空間合計 `200 GB`；ARM 預設 `100 GB`，剩下的空間剛好夠兩台 Micro（各 `50 GB`）。如果你還有其他磁碟，請把 `BOOT_VOLUME_SIZE_IN_GBS` 調小。

### Micro 腳本：`oci_retry_micro.py`

```python
COMPARTMENT_ID = ""  # 留空則使用 OCI 設定檔中的租用戶（根區間）
INSTANCE_NAME  = "micro-server"   # 搶第二台時改成 "micro-server-2"，方便在 OCI Console 區分
UBUNTU_VERSION = "24.04"  # 新機器安裝的作業系統："24.04"（預設）、"26.04" 或 "22.04"
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # 重試間隔（秒）
```

> 每個 OCI 帳號最多可以有 **2 台免費 Micro**。搶第二台時，將 `INSTANCE_NAME` 改成不同的名稱（例如 `"micro-server-2"`），方便在 OCI Console 區分。VCN 和子網路會自動共用，不需要另外建立。

> ⚠️ **有多個可用性網域（AD）的區域：** Oracle 官方 [Always Free 頁面](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)寫明 Micro 只能在其中一個 AD 建立，但沒有說是哪一個。腳本一律使用 API 回傳的**第一個** AD（`get_availability_domain()` 裡的 `ads[0]`）。如果你的區域有多個 AD，而 Micro 腳本一直搶不到，請到 OCI 主控台搜尋 **Limits, Quotas and Usage**，查看 Micro 的額度分配在哪個 AD，再把 `ads[0]` 改成那個 AD 的順序編號。只有一個 AD 的區域（例如 `ap-singapore-1`）不受影響。

### Ubuntu 版本（兩支腳本通用）

`UBUNTU_VERSION` 決定**新建立的機器**要安裝哪一版 Ubuntu LTS，腳本會自動挑該版本在 Oracle 上最新的映像檔。修改這個值只影響之後新建的機器，已經在運作的機器不會被改變。

| 版本 | 標準安全更新到 | 內建 Python |
|------|--------------|------------|
| `"26.04"` | 2031 年 5 月 | 3.14 |
| `"24.04"`（預設） | 2029 年 5 月 | 3.12 |
| `"22.04"` | 2027 年 5 月 | 3.10 |

資料來源：[Ubuntu 版本週期](https://ubuntu.com/about/release-cycle)、[python3-defaults](https://launchpad.net/ubuntu/+source/python3-defaults)。

### 取得 Compartment ID（租用戶 OCID）

**用途**：告訴 Oracle 要在哪個帳號下建立資源。只有想使用租用戶（根區間）以外的區間時才需要填，否則 `COMPARTMENT_ID` 留空即可

1. Oracle Cloud 主控台 → 右上角 **Profile** 選單 → **租用戶: XXX**
2. 或：左上角選單 → **識別與安全** → **身份識別** → **區間** → 點（根）root
3. 複製 OCID（格式：`ocid1.tenancy.oc1..xxxxxx`）

### 取得 SSH 公開金鑰

**用途**：建立 instance 後用來 SSH 連線進入 server

1. 在 Oracle Cloud 建立 instance 時，選「**產生金鑰組**」（Generate key pair）
2. 下載兩個檔案：
   - `*.key` 或 `*.pem`（私密金鑰，自己保管，連線時用）
   - `*.pub`（公開金鑰。GitHub Actions：內容要設定到 GitHub Secrets 的 `OCI_SSH_PUBLIC_KEY`，設定方式見「設定步驟」的 Step 3；本機執行：在 OCI 設定檔的 `ssh_public_key_file` 填入這個檔案的路徑）
3. 用記事本開啟 `.pub` 檔，複製全部內容（格式：`ssh-rsa AAAA...` 開頭）

或在本機執行 `ssh-keygen` 自己產生。

---

## 本機執行

### 1. 建立 OCI 設定檔

**儲存位置**：`~/.oci/config`（Windows 為 `C:\Users\你的帳號\.oci\config`；建立資料夾和檔案，檔案無副檔名）

```
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxxx
region=ap-singapore-1
key_file=C:\Users\你的帳號\Desktop\私密金鑰.pem
ssh_public_key_file=C:\Users\你的帳號\Desktop\ssh-key.pub
```

**取得設定檔內容**：
1. Oracle Cloud 主控台 → 右上角 **Profile** 選單 → **使用者設定值**（User settings）
2. 左側選單 → **我的設定檔**（My profile）→ 上方選單 → **權杖和金鑰**（Tokens and keys）→ **新增 API 金鑰**（Add API key）
3. 選「**產生 API 金鑰組**」（Generate API key pair）→ 下載私密金鑰（`.pem` 檔）
4. 按「新增」→ 複製出現的設定文字，貼入 `config` 檔
5. 把 `key_file` 的路徑改成 `.pem` 檔的實際存放位置
6. 確認 `region` 是你帳號的**主區域**，因為 Always Free 資源只能建立在主區域。查詢方式：點主控台右上角的區域名稱，選單會標出 **Home region**（例如 `Singapore (Singapore)`），再到 Oracle 的[區域列表](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)查出它的區域識別碼（Region Identifier，例如 `ap-singapore-1`）
7. 加上 `ssh_public_key_file`，填入你的 SSH 公開金鑰（`.pub`，見上方「取得 SSH 公開金鑰」）的路徑。腳本會把這把金鑰裝到新機器上

### 2. 調整腳本設定（選擇性）

機器名稱、Ubuntu 版本等設定都在腳本最上方，請見上方「腳本設定」。

### 3. 安裝套件並執行

```bash
# 安裝套件（只需一次）
pip install oci

# 執行 ARM 版
python oci_retry.py

# 執行 Micro 版
python oci_retry_micro.py
```

### 腳本執行行為

| 狀態 | 說明 |
|------|------|
| 初始化 | 自動建立 VCN + 子網路（已存在則跳過）|
| 搶機循環 | 每隔 `RETRY_INTERVAL` 秒嘗試一次 |
| 容量不足 | 印出 ❌ 並繼續重試 |
| 網路逾時 | 印出 ⚠️ 並繼續重試（不會當掉）|
| 建立機器時的其他錯誤（例如額度已滿）| 印出 ❌ 和錯誤訊息並繼續重試；如果一直不成功，請查看 log |
| 初始化錯誤（例如 OCID 或 API 金鑰填錯）| 在進入搶機循環前就出錯停止 |
| 成功 | 印出 ✅ instance ID 並自動停止 |

> **開放的 port：** 腳本建立新的 VCN 時，會對所有來源（`0.0.0.0/0`）開放 TCP **22（SSH）、80（HTTP）、443（HTTPS）**；如果 VCN 已經存在，則沿用原本的設定不做修改。需要其他 port 的話，可以在第一次執行前加進 `create_vcn_and_subnet()` 裡的 port 清單，或之後到 OCI 主控台，在 VCN 的安全清單（Security List）新增規則。另外，OCI 的 Ubuntu 映像檔還需要在機器的 `iptables` 放行該 port，做法請見 Oracle 官方 [Apache on Ubuntu 教學](https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/apache-on-ubuntu/01oci-ubuntu-apache-summary.htm)的「Update firewall settings」步驟。

---

## GitHub Actions 自動搶機（推薦）

不需要電腦一直開著，24 小時不間斷自動重試。

### 運作方式

```
Job 開始
  └─ 每 90 秒嘗試一次，持續約 330 分鐘（~220 次）
       ├─ 搶到了 → 自動停用 workflow，結束
       ├─ 腳本出錯（例如 secrets 填錯）→ 鏈條停止，並顯示錯誤訊息
       └─ timeout → 立刻觸發下一個 Job，空窗幾乎為零
                        └─ 重複循環...

鏈條中斷時：手動到 Actions 頁籤再按一次 Run workflow
```

| 項目 | 說明 |
|------|------|
| 每次 Job 持續時間 | 約 330 分鐘（~220 次嘗試）|
| 接力方式 | 時間到時自動觸發下一個，空窗幾乎為零 |
| 同時執行上限 | 最多 1 個跑 + 1 個排隊（不會累積）|
| 腳本出錯時 | 鏈條停止並顯示錯誤訊息；修正問題後再按一次 Run workflow |
| 鏈條中斷時 | 手動到 Actions 頁籤再按一次 Run workflow |
| 搶到後 | workflow 自動停用；如果停用失敗，執行結果會顯示「Auto-disable failed」錯誤，請手動停用 |
| ARM 與 Micro | 各自獨立的 workflow，**建議一次只跑一個** |

> ⚠️ 兩個 workflow 使用同一個 OCI 帳號。用預設的 `RETRY_INTERVAL`（90 秒）同時執行 ARM 和 Micro，OCI 會回傳 `TooManyRequests` 錯誤。建議不要同時啟動兩個 workflow。

---

## 設定步驟

### Step 1：建立 GitHub 倉庫

建立 **public** 倉庫（public 才有無限制的 Actions 分鐘數）。

### Step 2：產生 OCI API 金鑰

1. Oracle Cloud 主控台 → 右上角 **Profile** 選單 → **使用者設定值**（User settings）
2. 左側選單 → **我的設定檔**（My profile）→ 上方選單 → **權杖和金鑰**（Tokens and keys）→ **新增 API 金鑰**（Add API key）
3. 選「**產生 API 金鑰組**」（Generate API key pair）→ 下載私密金鑰（`.pem` 檔）
4. 按「新增」後複製出現的設定文字，從中取得以下值：
   - `user`、`fingerprint`、`tenancy`、`region`

### Step 3：設定 GitHub Secrets

到倉庫 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

共需設定 **6 個** secret：

| Secret 名稱 | 填入的值 | 取得位置 |
|------------|---------|----------|
| `OCI_USER` | `ocid1.user.oc1..xxxxxx` | OCI 主控台 → 我的設定檔 → OCID |
| `OCI_FINGERPRINT` | `xx:xx:xx:xx:xx` | OCI 主控台 → 我的設定檔 → API 金鑰 → 指紋 |
| `OCI_TENANCY` | `ocid1.tenancy.oc1..xxxxxx` | OCI 主控台 → 右上角 **Profile** 選單 → **租用戶: &lt;名稱&gt;** → OCID |
| `OCI_REGION` | 例如 `ap-singapore-1` | 你的**主區域**：點 OCI 主控台右上角的區域名稱，選單會標出 **Home region**（例如 `Singapore (Singapore)`），填入它的區域識別碼（例如 `ap-singapore-1`，見[區域列表](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)）。Always Free 資源只能建立在主區域 |
| `OCI_PRIVATE_KEY` | `.pem` 檔案完整內容 | 開啟 Step 2 下載的 `.pem` 檔，複製全部文字（含頭尾 `-----BEGIN/END PRIVATE KEY-----`）|
| `OCI_SSH_PUBLIC_KEY` | `.pub` 檔案完整內容 | 見上方「取得 SSH 公開金鑰」（以 `ssh-` 開頭）|

> 不需要另外建立 GitHub token：接力觸發下一個 Job 和自動停用，都是用 GitHub 每個 Job 自動產生的內建 `GITHUB_TOKEN`。

### Step 4：推送程式碼到 GitHub

```bash
git remote add origin https://github.com/你的帳號/你的倉庫名稱.git
git branch -M main
git push -u origin main
```

### Step 5：啟動 workflow

1. 到倉庫 → **Actions** 頁籤
2. 若 workflow 顯示停用，點 **Enable workflow**
3. 點 **Run workflow** 手動立刻觸發第一次

ARM 和 Micro 各自有獨立的 workflow，建議一次只啟動一個（原因見「運作方式」下方的說明）。

---

## 成功後

搶到 instance 後，workflow 會**自動停用**。如果執行結果顯示 **Auto-disable failed** 錯誤，請手動停用：Actions 頁籤 → 該 workflow → **...** → **Disable workflow**。

到 Oracle Cloud 主控台 → **Compute** → **執行處理** → 查看公用 IP，即可 SSH 連線：

```bash
ssh -i 私密金鑰.pem ubuntu@公用IP
```

---

## 注意事項

- `COMPARTMENT_ID` 寫在腳本裡是安全的（非機密資訊）
- OCI API 私密金鑰等敏感資訊全部放在 GitHub Secrets，不進版本控制
- **2026-11-07 更新：** workflow 不再使用 `GH_PAT` secret。如果你在這個日期之前 fork 或複製了這個 repo，請用這個 repo 目前的版本取代你的 `.github/workflows/oci_retry.yml` 和 `.github/workflows/oci_retry_micro.yml`（腳本不需要更新；如果連腳本也一起更新，請另外新增 GitHub Secrets 的 `OCI_SSH_PUBLIC_KEY`），之後就可以刪掉 `GH_PAT` secret，並到 GitHub → Settings → Developer settings 撤銷（revoke）那組 token
- `.pem` / `.key` / `.pub` 已加入 `.gitignore`，不會被 commit
