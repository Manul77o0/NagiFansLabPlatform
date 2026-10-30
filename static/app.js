const guestView = document.querySelector("#guest-view");
const userView = document.querySelector("#user-view");
const message = document.querySelector("#message");

function showGuest() {
    guestView.hidden = false;
    userView.hidden = true;
}

function showUser(user) {
    document.querySelector("#username-display").textContent = user.username;
    guestView.hidden = true;
    userView.hidden = false;
}

async function loadCurrentUser() {
    const response = await fetch("/users/me/");
    if (response.status === 401) {
        showGuest();
        return;
    }
    if (!response.ok) {
        throw new Error("ユーザー情報を取得できませんでした");
    }

    const user = await response.json();
    showUser(user);
    await loadItems();
}

async function loadItems() {
    const response = await fetch("/users/me/items/");
    if (!response.ok) {
        throw new Error("アイテムを取得できませんでした");
    }

    const items = await response.json();
    const list = document.querySelector("#items-list");
    list.replaceChildren(
        ...items.map((item) => {
            const element = document.createElement("li");
            element.textContent = `${item.item_id} (owner: ${item.owner})`;
            return element;
        }),
    );
}

document.querySelector("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    message.textContent = "";
    const loginForm = event.currentTarget;
    const form = new FormData(loginForm);

    try {
        const response = await fetch("/session/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: form.get("username"),
                password: form.get("password"),
            }),
        });
        if (response.status === 401) {
            message.textContent = "ユーザー名またはパスワードが正しくありません";
            return;
        }
        if (!response.ok) {
            throw new Error("ログインに失敗しました");
        }

        loginForm.reset();
        await loadCurrentUser();
    } catch (error) {
        message.textContent = error.message;
    }
});

document.querySelector("#logout-button").addEventListener("click", async () => {
    message.textContent = "";
    try {
        const response = await fetch("/session/logout", { method: "POST" });
        if (!response.ok) {
            throw new Error("ログアウトに失敗しました");
        }
        showGuest();
        document.querySelector("#items-list").replaceChildren();
    } catch (error) {
        message.textContent = error.message;
    }
});

loadCurrentUser().catch((error) => {
    message.textContent = error.message;
});
