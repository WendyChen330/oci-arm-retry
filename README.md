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
| GitHub Actions (recommended) | Long-term automated retrying | 24/7, no computer resources needed | Requires a **public** repo + Secrets setup |
| Run locally | Quick testing | No GitHub setup needed | Your computer must stay on |

> 💡 **Why public repo?** Public repositories get unlimited GitHub Actions minutes for free. Private repos have a monthly limit.

---

## Before You Start (Both Methods)

### Get an OCI API Key

1. OCI Console → top-right **Profile** menu → **User settings**
2. Left menu → **My profile** → top menu → **Tokens and keys** → **Add API key**
3. Choose **Generate API key pair** → download the private key (`.pem` file)
4. Click **Add** → a configuration snippet appears with your `user`, `fingerprint`, `tenancy` and `region`. Copy it and keep it with the `.pem` file; the next steps use these values

### Find Your Home Region

Always Free resources can only be created in your tenancy's **home region**. To find it, click the region name at the top right of the Console; the menu shows your **Home region** (e.g. `Singapore (Singapore)`). Its Region Identifier (e.g. `ap-singapore-1`, see Oracle's [region list](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)) is the `region` value to use.

### Get SSH Public Key

**Purpose**: Used to SSH into the instance after it's created.

1. When creating an instance in Oracle Cloud, choose **Generate key pair** (Generate SSH key pair)
2. Download two files:
   - `*.key` or `*.pem` (private key — keep this safe, used for SSH login)
   - `*.pub` (public key — GitHub Actions: add its contents as the `OCI_SSH_PUBLIC_KEY` GitHub Secret, see Step 2: Set GitHub Secrets; local runs: set `ssh_public_key_file` in your OCI config to this file)
3. Open the `.pub` file in a text editor, copy all content (starts with `ssh-rsa AAAA...`)

Or generate your own key locally with `ssh-keygen`.

### Script Configuration

The settings are at the top of each script. Edit them after you get the repository (GitHub Actions: Step 3; Run Locally: step 3):

#### ARM script: `oci_retry.py`

```python
INSTANCE_NAME = "arm-server"
UBUNTU_VERSION = "24.04"  # OS for the new instance: "24.04" (default), "26.04" or "22.04"
ARM_OCPUS = 2
ARM_MEMORY_IN_GBS = 12
BOOT_VOLUME_SIZE_IN_GBS = 100
RETRY_INTERVAL = 90  # Retry interval in seconds
```

> `BOOT_VOLUME_SIZE_IN_GBS` sets the boot volume size. Always Free includes `200 GB` of boot + block volume storage in total; the ARM default of `100 GB` leaves room for two Micro instances (`50 GB` each). Lower `BOOT_VOLUME_SIZE_IN_GBS` if you also use other volumes.

#### Micro script: `oci_retry_micro.py`

```python
INSTANCE_NAME  = "micro-server"   # Change to "micro-server-2" when claiming your second Micro instance
UBUNTU_VERSION = "24.04"  # OS for the new instance: "24.04" (default), "26.04" or "22.04"
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # Retry interval in seconds
```

> Each OCI account can have up to **2 free Micro instances**. To claim a second one, change `INSTANCE_NAME` to a different value (e.g. `"micro-server-2"`) so both instances can be identified separately in the OCI Console. The VCN and subnet are shared between instances automatically.

> ⚠️ **Regions with multiple availability domains (ADs):** Oracle's [Always Free page](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) states that Micro instances "can only be created in one availability domain", but does not say which one. The scripts always use the **first** AD returned by the API (`ads[0]` in `get_availability_domain()`). If your region has several ADs and the Micro script never succeeds, check your Micro limit per AD in the OCI Console (search for **Limits, Quotas and Usage**), then change `ads[0]` to the index of that AD. Regions with a single AD (e.g. `ap-singapore-1`) are not affected.

#### Ubuntu version (both scripts)

`UBUNTU_VERSION` sets which Ubuntu LTS is installed on the **new** instance. The script always picks the newest Oracle image build of that version. Changing it only affects instances created afterwards; instances you already have keep their OS.

| Version | Standard security updates until | Default Python |
|---------|-------------------------------|----------------|
| `"26.04"` | May 2031 | 3.14 |
| `"24.04"` (default) | May 2029 | 3.12 |
| `"22.04"` | May 2027 | 3.10 |

Sources: [Ubuntu release cycle](https://ubuntu.com/about/release-cycle), [python3-defaults](https://launchpad.net/ubuntu/+source/python3-defaults).

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

### Setup Steps

#### Step 1: Get This Repository

Click **Fork** at the top of this repository's page to copy it to your GitHub account. Keep it **public** (public repos get unlimited Actions minutes).

If you prefer to create your own **public** repository instead, create it empty (no README), then copy this code into it:

```bash
git clone https://github.com/WendyChen330/oci-arm-retry.git
cd oci-arm-retry
git remote set-url origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

#### Step 2: Set GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

You need **6 secrets** in total:

| Secret Name | Value | Where to Get It |
|-------------|-------|----------------|
| `OCI_USER` | `ocid1.user.oc1..xxxxxx` | `user` in the configuration snippet from **Get an OCI API Key** above |
| `OCI_FINGERPRINT` | `xx:xx:xx:xx:xx` | `fingerprint` in the configuration snippet from **Get an OCI API Key** above |
| `OCI_TENANCY` | `ocid1.tenancy.oc1..xxxxxx` | OCI Console → top-right **Profile** menu → **Tenancy: &lt;name&gt;** → OCID |
| `OCI_REGION` | e.g. `ap-singapore-1` | Your home region's Region Identifier, see **Find Your Home Region** above. Always Free resources can only be created there |
| `OCI_PRIVATE_KEY` | Full contents of `.pem` file | Open the `.pem` from **Get an OCI API Key** above, copy everything (including `-----BEGIN/END PRIVATE KEY-----`) |
| `OCI_SSH_PUBLIC_KEY` | Full contents of your `.pub` file | See **Get SSH Public Key** above (starts with `ssh-`) |

> No GitHub token is needed: relaying to the next Job and auto-disabling use the workflow's built-in `GITHUB_TOKEN`, which GitHub creates for each Job automatically.

#### Step 3: Adjust Script Settings (Optional)

To change the instance name, Ubuntu version or other settings, edit the variables at the top of the script in your repository and commit the change. See **Script Configuration** above.

#### Step 4: Start the Workflow

1. Go to your repository → **Actions** tab. On a new fork, first click the green **I understand my workflows, go ahead and enable them** button
2. In the left sidebar, select **OCI ARM Retry** or **OCI Micro Retry**, click **Run workflow** on the right, then click the green **Run workflow** button in the menu

ARM and Micro have separate workflows. Running only one at a time is recommended (see the note under How It Works).

---

## Run Locally

### 1. Download This Repository

Requires Python 3 with pip. Download this repository (**Code** → **Download ZIP**, or `git clone`) and open a terminal in its folder.

### 2. Create the OCI Config File

**Location**: `~/.oci/config` (on Windows: `C:\Users\<username>\.oci\config`, no file extension)

On Windows, you can create the folder and an empty file in PowerShell, then open it in Notepad:

```powershell
New-Item -ItemType Directory -Force "$HOME\.oci" | Out-Null
if (-not (Test-Path "$HOME\.oci\config")) { New-Item -ItemType File "$HOME\.oci\config" | Out-Null }
notepad "$HOME\.oci\config"
```

```
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxxx
region=ap-singapore-1
key_file=C:\Users\<username>\.oci\oci_api_key.pem
ssh_public_key_file=C:\Users\<username>\.oci\ssh-key.pub
```

1. Paste the configuration snippet from **Get an OCI API Key**
2. Update `key_file` to the actual path of your `.pem` file
3. Make sure `region` is your home region (see **Find Your Home Region**)
4. Add `ssh_public_key_file` with the path to your SSH public key (`.pub`, see **Get SSH Public Key**). The script installs this key on the new instance

> ⚠️ Use file paths with English letters and numbers only. On Windows, a path containing Chinese or other non-English characters can make the config file fail to load.

### 3. Adjust Script Settings (Optional)

Instance name, Ubuntu version and the other settings are at the top of each script. See **Script Configuration** above.

### 4. Install and Run

In that terminal, run:

```bash
# Install dependencies (once only)
pip install oci

# Run ARM version
python oci_retry.py

# Run Micro version
python oci_retry_micro.py
```

---

## Script Behavior

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

## After Success

Once an instance is claimed, the workflow **auto-disables**. If the run shows an **Auto-disable failed** error instead, disable it manually: Actions tab → the workflow → **...** → **Disable workflow**.

Go to OCI Console → **Compute** → **Instances** → find your instance's public IP, then SSH in:

```bash
ssh -i ssh-key.key ubuntu@your-public-ip
```

Use the SSH private key from **Get SSH Public Key** (not the OCI API key `.pem`).

---

## Notes

- Sensitive values (OCI API private key) are stored in GitHub Secrets and never committed
- **Change on November 7, 2026:** the workflows no longer use a `GH_PAT` secret. If you forked or copied this repo before that date, replace your `.github/workflows/oci_retry.yml` and `.github/workflows/oci_retry_micro.yml` with the current versions from this repo (the scripts don't need to change). After that, you can delete the `GH_PAT` secret and revoke the token in GitHub → Settings → Developer settings
- **Change on November 8, 2026:** `COMPARTMENT_ID` and `SSH_PUBLIC_KEY` are no longer settings in the scripts. Instances are now always created in your tenancy (root compartment), and the SSH public key is read from the `OCI_SSH_PUBLIC_KEY` GitHub Secret (GitHub Actions) or from `ssh_public_key_file` in your OCI config (local runs). If you update your copy of the scripts to this version: for GitHub Actions, also replace both `.yml` files in `.github/workflows/` and add that secret; for local runs, add that config entry
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

兩種機型都屬於 Oracle Always Free 永久免費方案。Always Free 的機器和磁碟都必須建立在租用戶（tenancy）的**主區域（home region）**。免費額度如下：

- **Ampere A1：** 每個租用戶合計 2 OCPU + 12 GB RAM
- **Micro：** 最多 2 台（每台 1/8 OCPU，可短暫使用更多 CPU）
- **儲存空間：** boot volume + block volume 合計 200 GB

> 📌 **官方更新（2026-06-15 起）：** Oracle 官方 Always Free 頁面將 Ampere A1 額度從 4 OCPU + 24 GB RAM 調降為每個租用戶 **2 OCPU + 12 GB RAM**。  
> 官方來源：https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

---

## 兩種使用方式

| 方式 | 適合對象 | 優點 | 缺點 |
|------|---------|------|------|
| GitHub Actions（推薦）| 長期自動搶機 | 24 小時不間斷，不佔電腦資源 | 需要 **public repo** + 設定 Secrets |
| 本機執行 | 想快速試試 | 不需要設定 GitHub | 電腦要一直開著 |

> 💡 **為什麼需要 public repo？** Public repo 可以免費使用無限制的 GitHub Actions 分鐘數。Private repo 每月有上限。

---

## 開始前的準備（兩種方式共用）

### 取得 OCI API 金鑰

1. OCI 主控台 → 右上角 **Profile** 選單 → **使用者設定值**（User settings）
2. 左側選單 → **我的設定檔**（My profile）→ 上方選單 → **權杖和金鑰**（Tokens and keys）→ **新增 API 金鑰**（Add API key）
3. 選 **產生 API 金鑰組**（Generate API key pair）→ 下載私密金鑰（`.pem` 檔）
4. 點 **新增**（Add）→ 畫面會出現一段設定文字，包含 `user`、`fingerprint`、`tenancy`、`region`。把它複製下來，跟 `.pem` 檔一起保存，後面的步驟會用到

### 查詢主區域

Always Free 資源只能建立在租用戶的**主區域**。查詢方式：點主控台右上角的區域名稱，選單會標出 **Home region**（例如 `Singapore (Singapore)`）。它的區域識別碼（Region Identifier，例如 `ap-singapore-1`，可對照 Oracle 的[區域列表](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)）就是 `region` 要填的值。

### 取得 SSH 公開金鑰

**用途**：建立 instance 後用來 SSH 連線進入 server

1. 在 Oracle Cloud 建立 instance 時，選「**產生金鑰組**」（Generate key pair）
2. 下載兩個檔案：
   - `*.key` 或 `*.pem`（私密金鑰，自己保管，連線時用）
   - `*.pub`（公開金鑰。GitHub Actions：內容要設定到 GitHub Secrets 的 `OCI_SSH_PUBLIC_KEY`，設定方式見「Step 2：設定 GitHub Secrets」；本機執行：在 OCI 設定檔的 `ssh_public_key_file` 填入這個檔案的路徑）
3. 用記事本開啟 `.pub` 檔，複製全部內容（格式：`ssh-rsa AAAA...` 開頭）

或在本機執行 `ssh-keygen` 自己產生。

### 腳本設定

設定都在每支腳本的最上方，取得 repo 之後再修改即可（GitHub Actions 見 Step 3；本機執行見步驟 3）：

#### ARM 腳本：`oci_retry.py`

```python
INSTANCE_NAME = "arm-server"
UBUNTU_VERSION = "24.04"  # 新機器安裝的作業系統："24.04"（預設）、"26.04" 或 "22.04"
ARM_OCPUS = 2
ARM_MEMORY_IN_GBS = 12
BOOT_VOLUME_SIZE_IN_GBS = 100
RETRY_INTERVAL = 90  # 重試間隔（秒）
```

> `BOOT_VOLUME_SIZE_IN_GBS` 是開機磁碟（boot volume）的大小。Always Free 的 boot volume + block volume 儲存空間合計 `200 GB`；ARM 預設 `100 GB`，剩下的空間剛好夠兩台 Micro（各 `50 GB`）。如果你還有其他磁碟，請把 `BOOT_VOLUME_SIZE_IN_GBS` 調小。

#### Micro 腳本：`oci_retry_micro.py`

```python
INSTANCE_NAME  = "micro-server"   # 搶第二台時改成 "micro-server-2"，方便在 OCI 主控台區分
UBUNTU_VERSION = "24.04"  # 新機器安裝的作業系統："24.04"（預設）、"26.04" 或 "22.04"
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # 重試間隔（秒）
```

> 每個 OCI 帳號最多可以有 **2 台免費 Micro**。搶第二台時，將 `INSTANCE_NAME` 改成不同的名稱（例如 `"micro-server-2"`），方便在 OCI 主控台區分。VCN 和子網路會自動共用，不需要另外建立。

> ⚠️ **有多個可用性網域（AD）的區域：** Oracle 官方 [Always Free 頁面](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)寫明 Micro 只能在其中一個 AD 建立，但沒有說是哪一個。腳本一律使用 API 回傳的**第一個** AD（`get_availability_domain()` 裡的 `ads[0]`）。如果你的區域有多個 AD，而 Micro 腳本一直搶不到，請到 OCI 主控台搜尋 **Limits, Quotas and Usage**，查看 Micro 的額度分配在哪個 AD，再把 `ads[0]` 改成那個 AD 的順序編號。只有一個 AD 的區域（例如 `ap-singapore-1`）不受影響。

#### Ubuntu 版本（兩支腳本通用）

`UBUNTU_VERSION` 決定**新建立的機器**要安裝哪一版 Ubuntu LTS，腳本會自動挑該版本在 Oracle 上最新的映像檔。修改這個值只影響之後新建的機器，已經建立的機器會維持原本的作業系統。

| 版本 | 標準安全更新到 | 內建 Python |
|------|--------------|------------|
| `"26.04"` | 2031 年 5 月 | 3.14 |
| `"24.04"`（預設） | 2029 年 5 月 | 3.12 |
| `"22.04"` | 2027 年 5 月 | 3.10 |

資料來源：[Ubuntu 版本週期](https://ubuntu.com/about/release-cycle)、[python3-defaults](https://launchpad.net/ubuntu/+source/python3-defaults)。

---

## GitHub Actions 自動搶機（推薦）

不需要電腦一直開著，24 小時不間斷自動重試。

### 運作方式

```
Job 開始
  └─ 每 90 秒嘗試一次，持續約 330 分鐘（~220 次）
       ├─ 搶到了 → 自動停用 workflow，結束
       ├─ 腳本出錯（例如 secrets 填錯）→ 鏈條停止，並顯示錯誤訊息
       └─ 逾時 → 立刻觸發下一個 Job，空窗幾乎為零
                        └─ 重複循環...

鏈條中斷時：手動到 Actions 頁籤再按一次 Run workflow
```

| 項目 | 說明 |
|------|------|
| 每次 Job 持續時間 | 約 330 分鐘（約 220 次嘗試）|
| 接力方式 | 時間到時自動觸發下一個，空窗幾乎為零 |
| 同時執行上限 | 最多 1 個跑 + 1 個排隊（不會累積）|
| 腳本出錯時 | 鏈條停止並顯示錯誤訊息；修正問題後再按一次 Run workflow |
| 鏈條中斷時 | 手動到 Actions 頁籤再按一次 Run workflow |
| 搶到後 | workflow 自動停用；如果停用失敗，執行結果會顯示「Auto-disable failed」錯誤，請手動停用 |
| ARM 與 Micro | 各自獨立的 workflow，**建議一次只跑一個** |

> ⚠️ 兩個 workflow 使用同一個 OCI 帳號。用預設的 `RETRY_INTERVAL`（90 秒）同時執行 ARM 和 Micro，OCI 會回傳 `TooManyRequests` 錯誤。建議不要同時啟動兩個 workflow。

### 設定步驟

#### Step 1：取得這個 repo

在這個 repo 頁面上方點 **Fork**，把它複製到你的 GitHub 帳號。請保持 **public**（public 才有無限制的 Actions 分鐘數）。

如果你想自己建立一個 **public** repo，請建立空的 repo（不要加 README），再把程式碼複製過去：

```bash
git clone https://github.com/WendyChen330/oci-arm-retry.git
cd oci-arm-retry
git remote set-url origin https://github.com/<你的 GitHub 帳號>/<repo 名稱>.git
git push -u origin main
```

#### Step 2：設定 GitHub Secrets

到 repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

共需設定 **6 個** secret：

| Secret 名稱 | 填入的值 | 取得位置 |
|------------|---------|----------|
| `OCI_USER` | `ocid1.user.oc1..xxxxxx` | 上方「取得 OCI API 金鑰」設定文字裡的 `user` |
| `OCI_FINGERPRINT` | `xx:xx:xx:xx:xx` | 上方「取得 OCI API 金鑰」設定文字裡的 `fingerprint` |
| `OCI_TENANCY` | `ocid1.tenancy.oc1..xxxxxx` | OCI 主控台 → 右上角 **Profile** 選單 → **租用戶: &lt;名稱&gt;** → OCID |
| `OCI_REGION` | 例如 `ap-singapore-1` | 主區域的區域識別碼，見上方「查詢主區域」。Always Free 資源只能建立在主區域 |
| `OCI_PRIVATE_KEY` | `.pem` 檔案完整內容 | 開啟上方「取得 OCI API 金鑰」下載的 `.pem` 檔，複製全部文字（含頭尾 `-----BEGIN/END PRIVATE KEY-----`）|
| `OCI_SSH_PUBLIC_KEY` | `.pub` 檔案完整內容 | 見上方「取得 SSH 公開金鑰」（以 `ssh-` 開頭）|

> 不需要另外建立 GitHub token：接力觸發下一個 Job 和自動停用，都是用 GitHub 每個 Job 自動產生的內建 `GITHUB_TOKEN`。

#### Step 3：調整腳本設定（選擇性）

想改機器名稱、Ubuntu 版本等設定，在你的 repo 裡修改腳本最上方的變數並 commit 即可，詳見上方「腳本設定」。

#### Step 4：啟動 workflow

1. 到 repo → **Actions** 頁籤。剛 fork 的 repo 要先點綠色的 **I understand my workflows, go ahead and enable them**
2. 在左側選 **OCI ARM Retry** 或 **OCI Micro Retry**，點右側的 **Run workflow**，再點選單裡綠色的 **Run workflow**

ARM 和 Micro 各自有獨立的 workflow，建議一次只啟動一個（原因見「運作方式」下方的說明）。

---

## 本機執行

### 1. 下載這個 repo

需要先安裝 Python 3 和 pip。下載這個 repo（**Code** → **Download ZIP**，或 `git clone`），並在它的資料夾開啟終端機。

### 2. 建立 OCI 設定檔

**儲存位置**：`~/.oci/config`（Windows 為 `C:\Users\<username>\.oci\config`，檔案沒有副檔名）

Windows 可以在 PowerShell 用下面的指令建立資料夾和空白檔案，再用記事本打開：

```powershell
New-Item -ItemType Directory -Force "$HOME\.oci" | Out-Null
if (-not (Test-Path "$HOME\.oci\config")) { New-Item -ItemType File "$HOME\.oci\config" | Out-Null }
notepad "$HOME\.oci\config"
```

```
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxxx
region=ap-singapore-1
key_file=C:\Users\<username>\.oci\oci_api_key.pem
ssh_public_key_file=C:\Users\<username>\.oci\ssh-key.pub
```

1. 貼上「取得 OCI API 金鑰」那段設定文字
2. 把 `key_file` 的路徑改成 `.pem` 檔的實際存放位置
3. 確認 `region` 是你的主區域（見「查詢主區域」）
4. 加上 `ssh_public_key_file`，填入你的 SSH 公開金鑰（`.pub`，見「取得 SSH 公開金鑰」）的路徑。腳本會把這把金鑰裝到新機器上

> ⚠️ 檔案路徑請只用英文和數字。在 Windows 上，路徑裡有中文等非英文字元，可能會讓設定檔讀取失敗。

### 3. 調整腳本設定（選擇性）

機器名稱、Ubuntu 版本等設定都在腳本最上方，請見上方「腳本設定」。

### 4. 安裝套件並執行

在這個終端機執行：

```bash
# 安裝套件（只需一次）
pip install oci

# 執行 ARM 版
python oci_retry.py

# 執行 Micro 版
python oci_retry_micro.py
```

---

## 腳本執行行為

| 狀態 | 說明 |
|------|------|
| 初始化 | 自動建立 VCN + 子網路（已存在則跳過）|
| 搶機循環 | 每隔 `RETRY_INTERVAL` 秒嘗試一次 |
| 容量不足 | 印出 ❌ 並繼續重試 |
| 網路逾時 | 印出 ⚠️ 並繼續重試（不會當掉）|
| 建立機器時的其他錯誤（例如額度已滿）| 印出 ❌ 和錯誤訊息並繼續重試；如果一直不成功，請查看 log |
| 初始化錯誤（例如 OCID 或 API 金鑰填錯）| 在進入搶機循環前就出錯停止 |
| 成功 | 印出 ✅ 機器 ID 並自動停止 |

> **開放的 port：** 腳本建立新的 VCN 時，會對所有來源（`0.0.0.0/0`）開放 TCP **22（SSH）、80（HTTP）、443（HTTPS）**；如果 VCN 已經存在，則沿用原本的設定不做修改。需要其他 port 的話，可以在第一次執行前加進 `create_vcn_and_subnet()` 裡的 port 清單，或之後到 OCI 主控台，在 VCN 的安全清單（Security List）新增輸入規則（ingress rule）。另外，OCI 的 Ubuntu 映像檔還需要在機器的 `iptables` 放行該 port，做法請見 Oracle 官方 [Apache on Ubuntu 教學](https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/apache-on-ubuntu/01oci-ubuntu-apache-summary.htm)的「Update firewall settings」步驟。

---

## 成功後

搶到機器後，workflow 會**自動停用**。如果執行結果顯示 **Auto-disable failed** 錯誤，請手動停用：Actions 頁籤 → 該 workflow → **...** → **Disable workflow**。

到 OCI 主控台 → **Compute** → **執行處理** → 查看公用 IP，即可 SSH 連線：

```bash
ssh -i ssh-key.key ubuntu@<公用 IP>
```

請用「取得 SSH 公開金鑰」那組的私密金鑰，不是 OCI API 的 `.pem`。

---

## 注意事項

- OCI API 私密金鑰等敏感資訊全部放在 GitHub Secrets，不進版本控制
- **2026-11-07 更新：** workflow 不再使用 `GH_PAT` secret。如果你在這個日期之前 fork 或複製了這個 repo，請用這個 repo 目前的版本取代你的 `.github/workflows/oci_retry.yml` 和 `.github/workflows/oci_retry_micro.yml`（腳本不需要更新），之後就可以刪掉 `GH_PAT` secret，並到 GitHub → Settings → Developer settings 撤銷（revoke）那組 token
- **2026-11-08 更新：** 腳本移除了 `COMPARTMENT_ID` 和 `SSH_PUBLIC_KEY` 兩個設定。機器現在一律建在你的租用戶（根區間），SSH 公開金鑰改從 GitHub Secrets 的 `OCI_SSH_PUBLIC_KEY`（GitHub Actions）或 OCI 設定檔的 `ssh_public_key_file`（本機執行）讀取。如果你要把自己的腳本更新到這個版本：GitHub Actions 請同時更新 `.github/workflows/` 裡的兩個 `.yml` 檔並新增這個 secret；本機執行請在設定檔加上這個欄位
- `.pem` / `.key` / `.pub` 已加入 `.gitignore`，不會被 commit
