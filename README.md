# Book Issue Desk

This is a small web app that runs on your own computer. It pretends to be the front desk of a comic-book shop. The shop has two customers, Alice and Bob.

The app does four things:

1. It saves a short text file of notes about a customer into Cognee. Cognee is a library and a service that stores text, turns it into a graph of facts, and lets you ask questions about it later. You can run Cognee on your own computer ("local mode") or use Cognee Cloud ("cloud mode"). The app works the same way in both.
2. It lets you click a ready-made question. Cognee reads only that customer's saved notes and sends back an answer.
3. It lets a customer sign in with Scalekit. Scalekit is a service that runs the login page for you. After login, Scalekit tells the app which customer is sitting at the browser. Scalekit can also post a message to Slack on behalf of that customer. The Slack password (called a token) stays inside Scalekit. The app never sees it, and Cognee never sees it.

Scalekit provides auth and actions on behalf of users, with 500+ connectors and 20,000+ tools.
4. It can index this repo's own source code into Cognee and answer structural questions about it ("what calls this function?", "draw the module map") without using an LLM.

The app runs at http://localhost:5001. "localhost" means your own computer.

Starting a hackathon on this repo? Read `.agents/skills/cognee-hackathon-kickoff/SKILL.md`. It is the 15-minute version of this README plus a list of project ideas. Agents that read `.claude/skills/` or `.agents/skills/` pick it up automatically.

## See Bob's failed payment come back

This is the fastest thing you can try. You do not need a Scalekit account for it. You do need either a Cognee Cloud account or an LLM API key (see [Choose where memory lives](#choose-where-memory-lives)).

1. Open http://localhost:5001
2. Click **Try Bob without login**
3. Click **Save this customer's notes**
4. Click the question about ordering the book again
5. The reply should say that Bob's last payment failed

What just happened: step 3 sent the file `fixtures/bob.txt` to Cognee and stored it under the name `bob`. Step 4 sent the question "I want to order the book again" to Cognee and told it to look only in `bob`. Cognee read Bob's notes, saw the line about the failed payment, and wrote an answer that mentions it.

The small badge next to the sign-in line tells you where this happened: "memory: Cognee Cloud" or "memory: local".

Login is the next section, after the desk is running. Slack is the last section and you can skip it.

![Bob memory recalls a failed payment](screenshots/06-desk-bob-guest-recall-payment.png)

## What Scalekit and Cognee do here

There are two text files in this repo: `fixtures/alice.txt` and `fixtures/bob.txt`. Each one is four lines long. They are the starting notes. They are **not** the memory. Nothing reads them when you ask a question.

When you click **Save this customer's notes**, the app reads the file and sends the text to Cognee. Cognee stores it in a "dataset" (a named bucket of saved text) called `alice` or `bob`. From then on, questions are answered from that dataset, not from the file.

Each customer has their own dataset. When Bob asks a question, Cognee looks only in `bob`. It never looks in `alice`. So Alice can never see Bob's payment problem, and Bob can never see what Alice is reading.

Scalekit's job is to answer the question "who is at the browser right now?". When Alice signs in, Scalekit sends the app a signed identity (a JWT, which is a small piece of text that proves who logged in). The app reads it, sees it is Alice, and picks the `alice` dataset.

If you click **Post to Slack**, the app asks Scalekit to send the message. Scalekit holds the Slack token and talks to Slack. The app only says "post this text to this channel as this customer".

![Sequence: Scalekit login, Cognee memory, Slack as Alice](screenshots/07-sequence-alice-scalekit-cognee-slack.png)

## Install uv and Python 3.12

`uv` is a tool that installs Python and Python packages quickly. Install it from [docs.astral.sh/uv](https://docs.astral.sh/uv/).

The app needs Python 3.12. Use `uv` to make a Python 3.12 virtual environment (a private folder with its own Python and packages, so nothing else on your computer is changed). The `python3` that Homebrew installs on some Macs is version 3.14. Version 3.14 will fail during install, so do not use it.

You also need a web browser and a terminal.

## Choose where memory lives

Cognee can run in two places. The app picks one when it starts and shows it in the badge on the page.

| Mode | What you need in `.env` | What happens |
|------|-------------------------|--------------|
| **Cloud** | `COGNEE_API_KEY` and `COGNEE_BASE_URL` | Every save and every question goes to your Cognee Cloud tenant. Nothing is stored on your computer. |
| **Local** | `LLM_API_KEY` (an OpenAI key by default) | The cognee Python library runs inside the app. It stores everything in small database files under `.venv`. It calls the LLM with your key to read the notes and to write answers. |
| **Local, then push** | all three | Same as local, plus a **Push this memory to Cloud** button. It uploads the finished graph to Cloud without calling the LLM again. |

Set `MEMORY_MODE=cloud` or `MEMORY_MODE=local` to choose. If you leave it empty, the app uses cloud when `COGNEE_BASE_URL` is filled in and local otherwise.

Local mode is the cheapest way to hack: you need no Cloud account, and you can delete `.venv` to start over. Cloud mode is what you want for a demo someone else will open.

Optional, local mode: `AUTO_FEEDBACK=false` makes answers come back faster. Without it, Cognee makes one extra LLM call after each answer to learn from the conversation.

## Create a Cognee Cloud account

Skip this section if you use local mode only.

The app needs a Cognee Cloud workspace to save notes and answer questions in cloud mode, and to receive a push in local mode.

1. Open [Create a Cognee account](https://docs.cognee.ai/cognee-cloud/sign-up).
2. Go to [platform.cognee.ai](https://platform.cognee.ai/sign-up).
3. Sign up with Google, GitHub, or email and password.
4. If you use email, open the verification link, then sign in.
5. Open **API Keys** in the sidebar.
6. Click **Create API key**.
7. Copy the key once. The console shows it only once. If you lose it, make a new one.
8. Copy the tenant base URL from the same page. It looks like `https://your-tenant.aws.cognee.ai`. Keep the `https://` part.

The API key is how the app proves to Cognee Cloud that it is allowed to use your workspace. The base URL is the address the app sends requests to.

Official guide: [Cognee Cloud sign-up](https://docs.cognee.ai/cognee-cloud/sign-up).

## Create a Scalekit account

Scalekit gives you an "environment" (a separate set of settings). You need one Development environment. It handles login. Later, the same environment can also hold the Slack connection.

| Job | When you need it | What you configure |
|-----|------------------|--------------------|
| Hosted login | After the desk is running, when Alice or Bob signs in | Redirect URLs, one-time passwords, test users |
| Slack posts as that customer | Last section, optional | A Slack connection in the same environment |

Do the login setup in this section. Slack setup is in [Post a status to Slack](#post-a-status-to-slack).

1. Open [app.scalekit.com](https://app.scalekit.com).
2. Create an account. Scalekit creates a Development environment for you.
3. Stay in **Development**. Do not switch to Production.
4. Open **Developers → Settings → API Credentials**.
5. Copy `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, and `SCALEKIT_CLIENT_SECRET`. These three values are how the app proves to Scalekit that it is your app.

Official guide: [Scalekit login quickstart](https://docs.scalekit.com/authenticate/fsa/quickstart/).

### Register localhost URLs

When someone logs in, Scalekit needs to send the browser back to your app. Scalekit only sends people to addresses you have written down first. Open **Authentication → Redirect URLs** and add these exact strings:

| Field | URL |
|-------|-----|
| Allowed callback URL | `http://localhost:5001/callback` |
| Initiate login URL | `http://localhost:5001/login` |
| Post logout URL | `http://localhost:5001/` |

The callback URL must be exactly the same, letter for letter, as `SCALEKIT_REDIRECT_URI` in your `.env` file. One extra slash or a different port and login will fail.

### Enable one-time passwords

A one-time password (OTP) is a short code you type instead of a normal password. Open **Authentication** and turn on **Magic Link & OTP**.

Set delivery to **Verification Code**, or to **Magic Link + Verification Code**. Do not pick Magic Link only. Magic Link only does not work with the test users set up in the next step.

### Add Alice and Bob as test users

A test user is a fake account that always accepts the same code. You never wait for an email.

1. Open **Environment settings → Test users**.
2. Turn test users on.
3. Add these two emails:

   - `alice+sktest@demo.com`
   - `bob+sktest@demo.com`

4. Set the static code to `424242`.
5. Save. Reload the page and check that both emails are still in the list.

Every test user email must have `+sktest` right before the `@`. Scalekit uses that to tell test users apart from real ones. Official guide: [Test users](https://docs.scalekit.com/authenticate/run-e2e-tests/).

After this section, Alice can log in. Slack still needs its own setup in the same environment (last section).

## Install the app

Run these commands in a terminal, one after the other:

```bash
git clone https://github.com/scalekit-developers/cognee-scalekit-example.git
cd cognee-scalekit-example
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
```

What each line does:

- `git clone` downloads this repo.
- `cd` moves into the downloaded folder.
- `uv venv` makes the Python 3.12 virtual environment in a folder called `.venv`.
- `uv pip install` installs the packages listed in `requirements.txt` (cognee, scalekit, fastapi, uvicorn, python-dotenv) into `.venv`.
- `cp .env.example .env` makes your own settings file by copying the example.

`.env` holds your secrets. It is listed in `.gitignore`, so git will not upload it. Do not commit it.

## Fill `.env`

Open `.env` in a text editor. Put each value you copied earlier on the matching line.

| Variable | Where you get it |
|----------|------------------|
| `MEMORY_MODE` | `cloud`, `local`, or empty (see [Choose where memory lives](#choose-where-memory-lives)) |
| `COGNEE_API_KEY` | Cognee console → API Keys (cloud mode, or to push) |
| `COGNEE_BASE_URL` | Same page. Keep the `https://` |
| `LLM_API_KEY` | Your OpenAI key (local mode only) |
| `SCALEKIT_ENVIRONMENT_URL` | Scalekit → Developers → Settings → API Credentials |
| `SCALEKIT_CLIENT_ID` | Same page |
| `SCALEKIT_CLIENT_SECRET` | Same page |
| `COOKIE_ENCRYPTION_SECRET` | Make one up by running `openssl rand -base64 32` in the terminal |
| `SCALEKIT_REDIRECT_URI` | Leave it as `http://localhost:5001/callback` |
| `CODE_REPO_URL` | Optional. A GitHub URL for **Index this repo**. Empty means this checkout (local) or this repo's public URL (cloud) |

`COOKIE_ENCRYPTION_SECRET` is a random string the app uses to scramble the login cookie (the small file the browser keeps so you stay logged in). Any long random string works. Nobody else needs to know it.

The Scalekit rows are always required. The app refuses to start without them, even in local memory mode, because the login routes are set up at startup.

## Start the desk

```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 5001
```

`uvicorn` is the program that runs the web app. `app:app` means "the object called `app` in the file `app.py`". The command keeps running until you press Ctrl+C.

Open http://localhost:5001 in a browser.

If you see "address already in use", another program is already using port 5001. Stop that program first, then run the command again.

## Ask Alice or Bob a question

The questions are fixed. You cannot type your own. Each customer has two buttons.

**Alice** is on the shop's Pro plan. Her saved notes say she is reading Avengers: Doomsday #51 and has not read #53. When she asks for #53, the reply should say she is on #51 and ask whether she wants to skip ahead to #53.

**Bob** is not on the Pro plan. His saved notes say his last payment failed and he still has an unpaid order. When he asks to order the book again, the reply should mention the failed payment and tell him to check it before placing a second order.

### Path 1 — Bob without login

Do this first. It does not touch Scalekit at all.

1. Click **Try Bob without login**. The app sets a cookie that says "this browser is Bob".
2. Click **Save this customer's notes**. This sends `fixtures/bob.txt` to Cognee (local or Cloud, per the badge). Wait until the page says it finished.
3. Click the fixed question. Wait. The reply comes from Cognee, live, right now.
4. The page says "guest Bob". This means nobody logged in. Scalekit was not involved.

### Path 2 — Alice with Scalekit

Do this after Path 1 works. Alice logs in through the page that Scalekit hosts.

1. Click **Sign in as Alice**. The browser goes to Scalekit's login page.
2. Type `alice+sktest@demo.com`.

   ![Scalekit hosted login for Alice](screenshots/03-scalekit-login-alice.png)

3. Type the code `424242`.
4. Scalekit sends the browser back to the app. If the app cannot tell from the login who you are, it shows a **Continue as Alice** button. Click it once.
5. Click **Save this customer's notes** if you have not saved Alice's notes before.
6. Click the fixed Avengers question. Wait. The reply comes from Alice's dataset only.

To try Bob through a real login instead of the guest button: log out, then sign in as `bob+sktest@demo.com` with the same code.

About step 4: the identity Scalekit sends back has a field called `sub` (a user id that looks like `usr_...`). By default it does **not** include the email address. That is normal. The app first checks whether `sub` matches `SCALEKIT_ALICE_SUB` or `SCALEKIT_BOB_SUB` in `.env`. If neither is set, it looks for "alice" or "bob" in any name or email fields that are present. If it still cannot tell, it asks you to pick.

If Alice never gets recognized automatically and you want to skip the **Continue as Alice** click: open the JWT panel on the page, copy her `sub` value, add the line `SCALEKIT_ALICE_SUB=usr_...` to `.env`, and restart the server.

## Push local memory to Cloud

Only in local mode, and only when `COGNEE_API_KEY` and `COGNEE_BASE_URL` are also filled in. Then the desk shows a **Push this memory to Cloud** button next to **Save this customer's notes**.

1. Save the customer's notes and ask a question, so the local graph exists.
2. Click **Push this memory to Cloud**.
3. The reply tells you how many nodes (facts) and edges (links between facts) were uploaded, and the name of the Cloud dataset they went into.

What it does: the app calls `cognee.push()`. That exports the customer's local graph into an archive, uploads the archive to your Cloud tenant, and the tenant imports it as-is. No LLM is called on the Cloud side, so pushing costs no tokens. Afterwards you can switch `.env` to `MEMORY_MODE=cloud`, restart, and ask the same question from Cloud.

If the push fails with "did not perform a COGX archive import", the Cloud tenant runs an older cognee that cannot import graphs. Use cloud mode and save the notes there instead.

## Index this repo's code

At the bottom of the page there is a **Code graph of this app** section. It works without a login and in both memory modes.

1. Click **Index this repo**. Cognee reads the source files, finds the functions, routes, and calls between them, and stores them as a graph in the dataset `desk_code`. No LLM is used for this.
2. Click one of the fixed questions:

   - **Draw the module map of this app** — a diagram of modules and HTTP routes.
   - **What breaks if I change require_customer()?** — every route and function that depends on that function, drawn and listed by distance.
   - **How does /api/ask reach Cognee recall?** — the call path from the route to `recall_user()`.
   - **What did the code analyzers flag?** — hotspots and findings, each with the code it points at.
   - **List the first indexed modules and symbols** — the raw facts.

Diagrams render in the page (Mermaid, loaded from a CDN). The raw result is shown below each diagram.

In local mode this indexes the checkout you are running. In cloud mode it sends this repo's GitHub URL and Cognee Cloud clones it. Set `CODE_REPO_URL` in `.env` to index a different public repository, then edit `CODE_QUESTIONS` in `loop.py` to ask about its functions.

## Post a status to Slack

Skip this section if you only want memory and login.

1. In the Scalekit dashboard, open **Connections**.
2. Add Slack. Name the connection `slack`. The app looks for a connection with exactly this name.
3. When the dashboard asks, connect your Slack account. Scalekit keeps the Slack token from this step.
4. In `.env`, set `SLACK_CHANNEL` to the channel name, without the `#`. Example: `general`.
5. In the desk, after you have a signed-in customer, click **Post to Slack**.

The first time, Scalekit may say the customer is not connected yet and give you a link. Open the link, approve, then click **Post to Slack** again.

The app never holds the Slack token. It tells Scalekit "post this text to this channel as this customer". Scalekit uses the stored token and sends the message to Slack.

![Alice status posted to Slack](screenshots/04-slack-pocket-agents-alice-status.png)

## If something fails

| What you see | What to do |
|--------------|------------|
| "missing env" error when starting | One of the required lines in `.env` is empty. Fill every row in the table above. Start uvicorn again. |
| "Redirect URI mismatch" | The callback URL in the Scalekit dashboard and `SCALEKIT_REDIRECT_URI` in `.env` are not exactly the same. Make them match. |
| The OTP email never arrives | Use the test-user emails and the code `424242`. Check that Magic Link & OTP is turned on. |
| Cognee gives an empty reply | The notes were not saved yet, or Cognee is still processing them. Click **Save this customer's notes**. Wait. Ask again. |
| "missing env for MEMORY_MODE=local" | Local mode needs `LLM_API_KEY`. Fill it, or switch to cloud mode. |
| Answers are slow in local mode | Add `AUTO_FEEDBACK=false` to `.env`. |
| "no code graph yet" | Click **Index this repo** first and wait for it to finish. |
| Python import errors | The virtual environment was made with the wrong Python. Delete `.venv` and run `uv venv --python 3.12 .venv` again. |
| "address already in use" | Another program is on port 5001. Stop it. |

## Run the CLI scripts

These are small terminal programs that do the same work as the web page, without the browser. They read the same `.env` file and the same `MEMORY_MODE`.

```bash
.venv/bin/python loop.py --user alice
.venv/bin/python loop.py --user bob
.venv/bin/python loop.py --user alice --push        # local mode: upload the graph to Cloud afterwards
.venv/bin/python loop.py --index-code               # build the code graph of this repo
.venv/bin/python loop.py --code architecture        # or: impact, path, insights, facts
.venv/bin/python slack_post.py --user alice --channel general --text "Acme renews 1 Nov. Refund window is 30 days."
```

`loop.py` connects to Cognee (Cloud or local), saves the customer's notes, waits for Cognee to finish building its memory, asks the fixed question, and prints the answer. With `--code` it prints the answer as text and, when there is a diagram, as a Mermaid code block you can paste into any Markdown viewer.

`slack_post.py` asks Scalekit to post the given text to the given channel as the given customer. If that customer has not connected Slack yet, it prints the link to connect.

## License

[MIT](LICENSE)

Scalekit docs: [login quickstart](https://docs.scalekit.com/authenticate/fsa/quickstart/).
Cognee docs: [Cloud sign-up](https://docs.cognee.ai/cognee-cloud/sign-up).
