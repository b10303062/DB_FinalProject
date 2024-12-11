# Steam-Together

## 專案簡介

有時候想要玩遊戲，但只有自己一個人怎麼辦？想要找尋志同道合的朋友一起體驗多人遊玩的樂趣、或是想要看看現在流行的遊戲有哪些，這時候就來使用線上遊戲大廳 「Steam together」 一起找尋玩伴吧！

「Steam together」 是一個線上遊玩房間配對的系統，在這個系統中使用者可以創建或加入別人的遊戲房間進行遊玩，創建房間時內可以選擇遊戲，吸引其他想玩相同遊戲的人加入房間。作為一次性的揪團活動，我們的目的是讓所有在系統的使用者都可以依據自己的喜好，找到一同玩樂的夥伴。

## 使用者功能

### General

系統中所有使用者都具備以下功能：

#### 註冊

- 使用者需要提供名稱、信箱、角色（User 或 Business Operator）與密碼。

- 註冊成功後，系統會發放一組 ID 給使用者。

#### 登入

- 使用者註冊帳號後才可登入。

- 登入時，使用者需要提供自己的 ID 與密碼。

### User

在我們的系統中，一般使用者（User）具有以下功能：

#### 搜尋遊戲

- 使用者可以根據遊戲名稱、遊戲種類、遊戲價格來搜尋資料庫中有紀錄的遊戲。搜尋結果會回傳遊戲名稱、遊戲 ID（由系統指定）、遊戲類型、發行日期、遊戲中可達成的成就數、正面評價數、負面評價評數。

#### 新增評論

- 使用者可以針對遊戲新增評論與評分（1 到 5 分）。需要注意的是，每位使用者針對一個遊戲只能發表一次評論，若要重新評論，需要先[刪除之前的評論](#刪除評論)。

- 進行評論時，需要提供遊戲 ID 與使用者的評分，使用者也可以提供文字評論。

- 若使用者在評論時，給予的評分達到 4 分，則系統會自動推薦 5 款同類型的遊戲。
  
#### 刪除評論

- 使用者可以刪除針對某個遊戲的評論。

- 刪除評論時，需要提供遊戲 ID。遊戲 ID 可透過[查詢遊戲](#搜尋遊戲)功能取得。

#### 將遊戲加入收藏

- 使用者可以將喜愛的遊戲加入收藏，其他使用者將能看到你的收藏。

- 加入收藏時，需要提供遊戲 ID。

#### 創建房間

- 使用者可以自由創建房間，並等待其他使用者進入。

- 創建房間時，需要提供房間名稱與欲遊玩的遊戲 ID。另外，使用者也可以設定房間的上限人數，預設為 10 人。
  
- 房間內支援聊天室功能，使用者可以發送文字訊息給房間內的其他使用者。自己發送的訊息會以粗體顯示、其他房客發送的訊息則以預設字型顯示、系統訊息則以黃色文字顯示。

- 房間內會顯示房間名稱、房間 ID、房主名稱、遊戲名稱與房間內當前人數。

- 使用者要離開房間時，須輸入 `\quit` 指令，該指令不會被視為聊天訊息並發送給其他使用者。

- 房間內有「房主」和「房客」兩種角色。創建房間者為房主，其他人則為房客。當房主離開房間時，房間就會被系統關閉，房間內所有成員都將自動退出。
 
#### 加入房間

- 使用者可以加入其他使用者創建的房間。

- 加入房間時，須提供房間 ID，房間 ID 可從[搜索房間](#搜索房間)功能取得。所有房間都有設置人數上限，若房間已滿則無法加入。

#### 查詢其他使用者資訊

- 使用者可以查詢其他使用者的資訊。

- 查詢時，須提供該使用者的 ID。

#### 搜索房間

- 使用者可以搜尋目前活躍中的房間。

- 搜尋房間時，可以提供遊戲類型，幫助使用者更快篩選出感興趣的房間。

#### 查看遊戲評論

- 使用者可以查看所有使用者對遊戲的評論。查看評論時，需要提供遊戲 ID。

### Admin（a.k.a Business Operator）

在我們的系統中，管理員（Admin）具有以下功能：

#### 新增遊戲

- 管理員可以新增遊戲。新增遊戲時，須提供遊戲名稱、發行日期。管理員也可以提供遊戲種類、遊戲價格、遊戲內總成就數、正面評價數、負面評價數。
  
- 新增完成後，該遊戲會被分配一組 ID。

#### 修改遊戲

- 管理員可以修改以加入系統的遊戲資訊。

- 修改遊戲時，須提供遊戲 ID。

#### 查詢遊戲

- 此功能與 User 的查詢遊戲功能相同。

#### 刪除遊戲

- 管理員可以刪除以加入系統的遊戲。
  
- 刪除遊戲時，須提供遊戲 ID。

#### 修改使用者資訊

- 管理員可以修改所有使用者的資訊，包括使用者名稱、信箱、密碼。

- 修改使用者資訊時，須提供使用者 ID。

## 使用說明

### 開發環境

- Ubuntu 24.04

- Python 3.12.4
  
  - psycopg 3.2.3

- PostgreSQL 16.6

已知環境問題：在我們的系統中，遊戲房間使用 select 函式進行實作，然而 Windows 系統未使用 「Everything is a file」 的思維，故 Winsock 函式庫的 select 函式不能對 non-socket objects（例如 stdin）進行操作，因此我們的系統須在 Linux 環境下執行，否則可能會發生無法進入房間的狀況。參考資料：[Python 的 select 函式官方文檔](https://docs.python.org/3/library/select.html#:~:text=Note%20that%20on%20Windows%2C%20it%20only%20works%20for%20sockets)。
 
### 建立資料庫

首先，使用 `Steam-Together.backup` 復原資料庫。

創建資料庫：
```
createdb <dbname> 
```

從 backup 檔復原資料庫：
```
pg_restore -d <dbname> < Steam-Together.backup
```

### 啟動伺服器

先使用以下指令啟動伺服器：
```
python src/server.py [--port <port>] [--pg_host <PGhost>] [--pg_port <PGport>] [--pg_user <PGuser>] [--pg_password <PGpassword>] [--pg_dbname <PGdbname>]
```
參數說明：

`--port`: 伺服器綁定的 port。預設為 **8888**。

`--pg_host`: PostgreSQL 伺服器所在的 host。預設為 **127.0.0.1**

`--pg_port`: PostgreSQL 伺服器綁定的 port。 預設為 **5432**。

`--pg_user`: PostgreSQL 的使用者名稱。預設為 **postgres**。

`--pg_password`: PostgreSQL 的使用者密碼。預設為 **postgres**。

`--pg_dbname`: PostgreSQL 資料庫的名稱。此名稱應與[建立資料庫](#建立資料庫)時使用的名稱相同。預設值為 `Steam-Together`。

### 連接伺服器

再使用以下指令啟動客戶端並連接伺服器：
```
python src/client.py [--host <host>] [--port <port>]
```
參數說明：

`--host`: 伺服器所在的 host。預設為 **127.0.0.1**。

`--port`: 伺服器綁定的 port。預設為 **8888**。

## 參考資料

本專案使用了以下公開資料集：

Antoni Sobkowicz. (2017). Steam Review Dataset [Data set]. Kaggle. [https://www.kaggle.com/datasets/andrewmvd/steam-reviews/data](https://www.kaggle.com/datasets/andrewmvd/steam-reviews/data)

• Nik Davis. (2019). Steam Store Games (Clean dataset) [Data set]. Kaggle. [https://www.kaggle.com/datasets/nikdavis/steam-store-games/data](https://www.kaggle.com/datasets/nikdavis/steam-store-games/data)