# OCI Free VM Retry Script | OCI 免費 VM 搶機腳本

Automated retry scripts to claim Oracle Cloud Always Free VMs (ARM A1.Flex / x86 E2.1.Micro) via GitHub Actions — no need to keep your computer on 24/7.

🌐 [English](#english) | [繁體中文](#繁體中文)

---

<a name="english"></a>
# English

## Two Scripts

| Script | Instance Type | Spec | Architecture |
|--------|--------------|------|--------------|
| `oci_retry.py` | VM.Standard.A1.Flex | 1 OCPU / 6 GB RAM / 100 GB disk | ARM (Ampere / aarch64) |
| `oci_retry_micro.py` | VM.Standard.E2.1.Micro | 1 OCPU / 1 GB RAM / 50 GB disk | x86 |

Both are part of the Oracle Always Free tier. The ARM script uses half of Oracle's documented Always Free Ampere A1 allowance: 1 OCPU + 6 GB memory. Micro remains available for up to 2 instances.

> 📌 **Always Free reference (June 15, 2026):** Oracle's official Always Free page documents Ampere A1 as **2 OCPUs + 12 GB RAM** per tenancy, and free boot volume + block volume storage as **200 GB total per region**.
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

The scripts read account-specific values from environment variables. In GitHub Actions, set the matching repository secrets listed below.

### ARM script: `oci_retry.py`

```python
ARM_OCPUS = 1
ARM_MEMORY_IN_GBS = 6
BOOT_VOLUME_SIZE_IN_GBS = 100
RETRY_INTERVAL = 90  # Retry interval in seconds
```

For local runs, export `OCI_COMPARTMENT_ID`, `OCI_SSH_PUBLIC_KEY`, and optionally `OCI_INSTANCE_NAME` before starting the script.

> The ARM script now exposes `BOOT_VOLUME_SIZE_IN_GBS` as a configuration variable. The default is `100 GB`, which is safer under the Always Free `200 GB` regional storage quota than the old `200 GB` default.

### Micro script: `oci_retry_micro.py`

```python
COMPARTMENT_ID = "ocid1.tenancy.oc1..your-ocid"
SSH_PUBLIC_KEY = "ssh-rsa AAAA...your-public-key"
INSTANCE_NAME  = "micro-server"   # Change to "micro-server-2" when claiming your second Micro instance
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # Retry interval in seconds
```

> Each OCI account can have up to **2 free Micro instances**. To claim a second one, change `INSTANCE_NAME` to a different value (e.g. `"micro-server-2"`) so both instances can be identified separately in the OCI Console. The VCN and subnet are shared between instances automatically.

### Get Compartment ID (Tenancy OCID)

**Purpose**: Tells Oracle which account to create resources under.

1. Oracle Cloud Console → top-right avatar → **Tenancy: XXX**
2. Or: top-left menu → **Identity & Security** → **Identity** → **Compartments** → click root
3. Copy the OCID (format: `ocid1.tenancy.oc1..xxxxxx`)

### Get SSH Public Key

**Purpose**: Used to SSH into the instance after it's created.

1. When creating an instance in Oracle Cloud, choose **Generate key pair** (Generate SSH key pair)
2. Download two files:
   - `*.key` or `*.pem` (private key — keep this safe, used for SSH login)
   - `*.pub` (public key — paste into the script)
3. Open the `.pub` file in a text editor, copy all content (starts with `ssh-rsa AAAA...`)

Or generate your own key locally with `ssh-keygen`.

---

## Run Locally

```bash
# Create an isolated environment and install the pinned OCI SDK
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --requirement requirements.txt

# Copy .env.example to .env, replace its placeholders, then load it
cp .env.example .env
set -a
. .env
set +a

# Run ARM version
python oci_retry.py

# Run Micro version
python oci_retry_micro.py
```

Run the offline configuration checks with:

```bash
make test
```

### Local OCI Config File Required

**Location**: `~/.oci/config` (on Windows: `C:\Users\YourName\.oci\config`, no file extension)

```
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxxx
region=ap-singapore-1
key_file=C:\Users\YourName\Desktop\private-key.pem
```

**How to get config values**:
1. Oracle Cloud Console → top-right avatar → **User settings**
2. Left menu → **My profile** → top menu → **Tokens and keys** → **Add API key**
3. Choose **Generate API key pair** → download the private key (`.pem` file)
4. Click **Add** → copy the configuration snippet that appears, paste it into your `config` file
5. Update `key_file` to the actual path of your `.pem` file

### Script Behavior

| Status | Description |
|--------|-------------|
| Initializing | Auto-creates VCN + subnet (skips if already exists) |
| Retry loop | Attempts every `RETRY_INTERVAL` seconds |
| Out of capacity | Prints ❌ and keeps retrying |
| Network timeout | Prints ⚠️ and keeps retrying (won't crash) |
| Success | Prints ✅ instance ID and stops automatically |

---

## Container build and run

```bash
docker build --tag oci-arm-retry .
docker run --rm \
  --env-file .env \
  --volume "$HOME/.oci:/root/.oci:ro" \
  oci-arm-retry
```

The container runs the ARM retry script by default. It uses the pinned dependency in `requirements.txt` and the mounted OCI config for authentication.

---

## GitHub Actions — Automated 24/7 Retry (Recommended)

No need to keep your computer running. GitHub Actions retries continuously, 24 hours a day.

### How It Works

```
Job starts
  └─ Attempts every 90 seconds for ~330 minutes (~220 tries)
       ├─ Instance claimed → workflow auto-disables, done
       └─ Timeout → immediately triggers next Job (virtually no gap)
                        └─ Repeats...

If the chain breaks: manually go to the Actions tab and click Run workflow again
```

| Item | Details |
|------|---------|
| Duration per Job | ~330 minutes (~220 attempts) |
| Relay method | Auto-triggers next Job on exit, virtually no gap |
| Max concurrency | 1 running + 1 queued (no pile-up) |
| If chain breaks | Manually trigger from Actions tab |
| After success | Workflow auto-disables — no manual action needed |
| ARM vs Micro | Separate workflows, can run simultaneously |

---

## Setup Steps

### Step 1: Create a GitHub Repository

Create a **public** repository (public repos get unlimited Actions minutes).

### Step 2: Generate OCI API Key

1. Oracle Cloud Console → top-right avatar → **User settings**
2. Left menu → **My profile** → top menu → **Tokens and keys** → **Add API key**
3. Choose **Generate API key pair** → download the private key (`.pem` file)
4. Click **Add** → from the configuration snippet, note these values:
   - `user`, `fingerprint`, `tenancy`, `region`

### Step 3: Set GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

You need **7 secrets** in total:

| Secret Name | Value | Where to Get It |
|-------------|-------|----------------|
| `OCI_USER` | `ocid1.user.oc1..xxxxxx` | Oracle Console → My profile → OCID |
| `OCI_FINGERPRINT` | `xx:xx:xx:xx:xx` | Oracle Console → My profile → API keys → Fingerprint |
| `OCI_TENANCY` | `ocid1.tenancy.oc1..xxxxxx` | Oracle Console → My profile → Tenancy OCID |
| `OCI_REGION` | e.g. `ap-singapore-1` | Oracle Console top-right region name |
| `OCI_PRIVATE_KEY` | Full contents of `.pem` file | Open the `.pem` from Step 2, copy everything (including `-----BEGIN/END PRIVATE KEY-----`) |
| `OCI_COMPARTMENT_ID` | Tenancy or compartment OCID | The compartment where the instance and network will be created |
| `OCI_SSH_PUBLIC_KEY` | Full contents of your SSH `.pub` file | The public key installed on the new instance |

The workflow uses GitHub's built-in token with `actions: write` permission to relay the next run and disable itself after success. No `GH_PAT` is required.

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

ARM and Micro have separate workflows and can run simultaneously.

---

## After Success

Once an instance is claimed, the workflow **auto-disables** — no manual action needed.

Go to Oracle Cloud Console → **Compute** → **Instances** → find your instance's public IP, then SSH in:

```bash
ssh -i private-key.pem ubuntu@your-public-ip
```

---

## Notes

- OCI API credentials, the compartment ID, and SSH public key are stored in GitHub Secrets and never committed
- `.pem` / `.key` / `.pub` files are in `.gitignore` and won't be tracked

---
---

<a name="繁體中文"></a>
# 繁體中文

## 兩種腳本

| 腳本 | 目標機型 | 規格 | 架構 |
|------|---------|------|------|
| `oci_retry.py` | VM.Standard.A1.Flex | 1 OCPU / 6 GB RAM / 100 GB 磁碟 | ARM (Ampere / aarch64) |
| `oci_retry_micro.py` | VM.Standard.E2.1.Micro | 1 OCPU / 1 GB RAM / 50 GB 磁碟 | x86 |

兩種都是 Oracle Always Free 永久免費方案。ARM 腳本使用 Oracle 官方 Always Free Ampere A1 配額的一半：`1 OCPU + 6 GB RAM`，Micro 則仍可最多建立 2 台。

> 📌 **官方參考（2026-06-15 起）：** Oracle 官方 Always Free 頁面明確寫明 Ampere A1 為每個 tenancy **2 OCPU + 12 GB RAM**，而免費的 boot volume + block volume 儲存總額則是 **每個 region 共 200 GB**。
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

腳本會從環境變數讀取帳號相關設定；在 GitHub Actions 中，請設定下方列出的 repository secrets。

### ARM 腳本：`oci_retry.py`

```python
ARM_OCPUS = 1
ARM_MEMORY_IN_GBS = 6
BOOT_VOLUME_SIZE_IN_GBS = 100
RETRY_INTERVAL = 90  # 重試間隔（秒）
```

本機執行前，請先設定 `OCI_COMPARTMENT_ID`、`OCI_SSH_PUBLIC_KEY`，以及可選的 `OCI_INSTANCE_NAME` 環境變數。

> ARM 腳本現在把 `BOOT_VOLUME_SIZE_IN_GBS` 抽成可調整的設定變數，預設為 `100 GB`。這比舊版 `200 GB` 更安全，較不容易一次把 Always Free 的 `200 GB` 區域儲存額度吃滿。

### Micro 腳本：`oci_retry_micro.py`

```python
COMPARTMENT_ID = "ocid1.tenancy.oc1..你的OCID"
SSH_PUBLIC_KEY = "ssh-rsa AAAA...你的公開金鑰內容"
INSTANCE_NAME  = "micro-server"   # 搶第二台時改成 "micro-server-2"，方便在 OCI Console 區分
BOOT_VOLUME_SIZE_IN_GBS = 50
RETRY_INTERVAL = 90  # 重試間隔（秒）
```

> 每個 OCI 帳號最多可以有 **2 台免費 Micro**。搶第二台時，將 `INSTANCE_NAME` 改成不同的名稱（例如 `"micro-server-2"`），方便在 OCI Console 區分。VCN 和子網路會自動共用，不需要另外建立。

### 取得 Compartment ID（租用戶 OCID）

**用途**：告訴 Oracle 要在哪個帳號下建立資源

1. Oracle Cloud 主控台 → 右上角頭像 → **租用戶: XXX**
2. 或：左上角選單 → **識別與安全** → **身份識別** → **區間** → 點（根）root
3. 複製 OCID（格式：`ocid1.tenancy.oc1..xxxxxx`）

### 取得 SSH 公開金鑰

**用途**：建立 instance 後用來 SSH 連線進入 server

1. 在 Oracle Cloud 建立 instance 時，選「**產生金鑰組**」（Generate key pair）
2. 下載兩個檔案：
   - `*.key` 或 `*.pem`（私密金鑰，自己保管，連線時用）
   - `*.pub`（公開金鑰，填入腳本）
3. 用記事本開啟 `.pub` 檔，複製全部內容（格式：`ssh-rsa AAAA...` 開頭）

或在本機執行 `ssh-keygen` 自己產生。

---

## 本機執行

```bash
# 安裝套件（只需一次）
pip install oci

# 執行 ARM 版
python oci_retry.py

# 執行 Micro 版
python oci_retry_micro.py
```

### 本機執行需要 OCI 設定檔

**儲存位置**：`C:\Users\你的帳號\.oci\config`（建立資料夾和檔案，檔案無副檔名）

```
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxxx
region=ap-singapore-1
key_file=C:\Users\你的帳號\Desktop\私密金鑰.pem
```

**取得設定檔內容**：
1. Oracle Cloud 主控台 → 右上角頭像 → **使用者設定值**（User settings）
2. 左側選單 → **我的設定檔**（My profile）→ 上方選單 → **權杖和金鑰**（Tokens and keys）→ **新增 API 金鑰**（Add API key）
3. 選「**產生 API 金鑰組**」（Generate API key pair）→ 下載私密金鑰（`.pem` 檔）
4. 按「新增」→ 複製出現的設定文字，貼入 `config` 檔
5. 把 `key_file` 的路徑改成 `.pem` 檔的實際存放位置

### 腳本執行行為

| 狀態 | 說明 |
|------|------|
| 初始化 | 自動建立 VCN + 子網路（已存在則跳過）|
| 搶機循環 | 每隔 `RETRY_INTERVAL` 秒嘗試一次 |
| 容量不足 | 印出 ❌ 並繼續重試 |
| 網路逾時 | 印出 ⚠️ 並繼續重試（不會當掉）|
| 成功 | 印出 ✅ instance ID 並自動停止 |

---

## GitHub Actions 自動搶機（推薦）

不需要電腦一直開著，24 小時不間斷自動重試。

### 運作方式

```
Job 開始
  └─ 每 90 秒嘗試一次，持續約 330 分鐘（~220 次）
       ├─ 搶到了 → 自動停用 workflow，結束
       └─ timeout → 立刻觸發下一個 Job，空窗幾乎為零
                        └─ 重複循環...

鏈條中斷時：手動到 Actions 頁籤再按一次 Run workflow
```

| 項目 | 說明 |
|------|------|
| 每次 Job 持續時間 | 約 330 分鐘（~220 次嘗試）|
| 接力方式 | Job 結束時自動觸發下一個，空窗幾乎為零 |
| 同時執行上限 | 最多 1 個跑 + 1 個排隊（不會累積）|
| 鏈條中斷時 | 手動到 Actions 頁籤再按一次 Run workflow |
| 搶到後 | workflow 自動停用，完全不需要手動操作 |
| ARM 與 Micro | 各自獨立 workflow，可同時執行互不干擾 |

---

## 設定步驟

### Step 1：建立 GitHub 倉庫

建立 **public** 倉庫（public 才有無限制的 Actions 分鐘數）。

### Step 2：產生 OCI API 金鑰

1. Oracle Cloud 主控台 → 右上角頭像 → **使用者設定值**（User settings）
2. 左側選單 → **我的設定檔**（My profile）→ 上方選單 → **權杖和金鑰**（Tokens and keys）→ **新增 API 金鑰**（Add API key）
3. 選「**產生 API 金鑰組**」（Generate API key pair）→ 下載私密金鑰（`.pem` 檔）
4. 按「新增」後複製出現的設定文字，從中取得以下值：
   - `user`、`fingerprint`、`tenancy`、`region`

### Step 3：設定 GitHub Secrets

到倉庫 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

共需設定 **7 個** secret：

| Secret 名稱 | 填入的值 | 取得位置 |
|------------|---------|----------|
| `OCI_USER` | `ocid1.user.oc1..xxxxxx` | OCI 主控台 → 我的設定檔 → OCID |
| `OCI_FINGERPRINT` | `xx:xx:xx:xx:xx` | OCI 主控台 → 我的設定檔 → API 金鑰 → 指紋 |
| `OCI_TENANCY` | `ocid1.tenancy.oc1..xxxxxx` | OCI 主控台 → 右上角頭像 → 租用戶: XXX → 租用戶 OCID |
| `OCI_REGION` | 例如 `ap-singapore-1` | OCI 主控台右上角區域名稱 |
| `OCI_PRIVATE_KEY` | `.pem` 檔案完整內容 | 開啟 Step 2 下載的 `.pem` 檔，複製全部文字（含頭尾 `-----BEGIN/END PRIVATE KEY-----`）|
| `OCI_COMPARTMENT_ID` | 租用戶或 compartment OCID | 建立 instance 和網路資源的 compartment |
| `OCI_SSH_PUBLIC_KEY` | SSH `.pub` 檔案完整內容 | 安裝到新 instance 的公開金鑰 |

workflow 使用具備 `actions: write` 權限的 GitHub 內建 token 接力下一次執行，成功後也會自動停用自己，不需要 `GH_PAT`。

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

ARM 和 Micro 各自有獨立的 workflow，可以同時啟動。

---

## 成功後

搶到 instance 後，workflow 會**自動停用**，不需要任何手動操作。

到 Oracle Cloud 主控台 → **Compute** → **執行處理** → 查看公用 IP，即可 SSH 連線：

```bash
ssh -i 私密金鑰.pem ubuntu@公用IP
```

---

## 注意事項

- OCI API 憑證、compartment ID 和 SSH 公開金鑰全部放在 GitHub Secrets，不進版本控制
- `.pem` / `.key` / `.pub` 已加入 `.gitignore`，不會被 commit
