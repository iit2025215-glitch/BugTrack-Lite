const $ = (id) => document.getElementById(id);

const issueModal = $("issue-modal");
const detailModal = $("detail-modal");
const form = $("issue-form");

let activeBugId = null;
let toastTimer;


function toast(message) {
    const el = $("toast");

    el.textContent = message;
    el.classList.add("show");

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {
        el.classList.remove("show");
    }, 2600);
}


function openModal(el) {
    el.classList.add("open");
    el.setAttribute("aria-hidden", "false");
}


function closeModal(el) {
    el.classList.remove("open");
    el.setAttribute("aria-hidden", "true");
}


function resetForm() {
    form.reset();

    activeBugId = null;
    $("bug-id").value = "";

    $("modal-title").textContent = "Report an issue";
    $("modal-eyebrow").textContent = "NEW ISSUE";
    $("save-btn").textContent = "Create issue";
}


function openCreate() {
    resetForm();
    openModal(issueModal);
}


function fillForm(bug) {
    activeBugId = bug.id;

    $("bug-id").value = bug.id;
    $("title").value = bug.title;
    $("description").value = bug.description;
    $("project").value = bug.project;
    $("severity").value = bug.severity;
    $("assigned-to").value = bug.assigned_to || "";

    $("modal-title").textContent = "Edit issue";
    $("modal-eyebrow").textContent = `EDIT ISSUE #${bug.id}`;
    $("save-btn").textContent = "Save changes";

    openModal(issueModal);
}


async function request(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
    }

    return data;
}


async function loadBug(id) {
    return request(`/api/bugs/${id}`);
}


function safe(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[ch]));
}


async function showDetails(id) {
    try {
        const bug = await loadBug(id);

        $("detail-title").textContent = `#${bug.id} ${bug.title}`;

        const comments = (bug.comments || []).map(comment => `
            <div class="comment-item">
                <b>${safe(comment.author)}</b>:
                ${safe(comment.body)}

                <small>
                    ${safe(comment.created_at)}
                </small>
            </div>
        `).join("") || `
            <p class="muted">No comments yet.</p>
        `;

        const activity = (bug.activity || []).map(item => `
            <div class="activity-item">
                ${safe(item.message)}

                <small>
                    ${safe(item.created_at)}
                </small>
            </div>
        `).join("") || `
            <p class="muted">No activity yet.</p>
        `;

        $("detail-content").innerHTML = `
            <div class="detail-meta">

                <span class="severity ${safe(bug.severity.toLowerCase())}">
                    ${safe(bug.severity)}
                </span>

                <span>
                    Status:
                    <b>${safe(bug.status)}</b>
                </span>

                <span>
                    Project:
                    <b>${safe(bug.project)}</b>
                </span>

                <span>
                    Assignee:
                    <b>${safe(bug.assigned_to || "Unassigned")}</b>
                </span>

            </div>

            <div class="detail-description">
                ${safe(bug.description)}
            </div>

            <div class="detail-meta">

                <span>
                    Reported by ${safe(bug.reported_by || "You")}
                </span>

                <span>
                    Created ${safe(bug.created_at)}
                </span>

                <span>
                    Updated ${safe(bug.updated_at)}
                </span>

            </div>

            <section class="detail-section">

                <h3>Comments</h3>

                <div id="comments-list">
                    ${comments}
                </div>

                <form class="comment-form" id="comment-form">

                    <input
                        id="comment-body"
                        placeholder="Write a comment..."
                        required
                        maxlength="1000"
                    >

                    <button type="submit">
                        Add
                    </button>

                </form>

            </section>

            <section class="detail-section">

                <h3>Activity history</h3>

                ${activity}

            </section>
        `;

        $("comment-form").addEventListener("submit", async event => {
            event.preventDefault();

            const body = $("comment-body").value.trim();

            if (!body) {
                return;
            }

            try {
                await request(`/api/bugs/${id}/comments`, {
                    method: "POST",
                    body: JSON.stringify({
                        body: body,
                        author: "You"
                    })
                });

                toast("Comment added");

                await showDetails(id);

            } catch (error) {
                toast(error.message);
            }
        });

        openModal(detailModal);

    } catch (error) {
        toast(error.message);
    }
}


/* Create and edit issue */

form.addEventListener("submit", async event => {
    event.preventDefault();

    const payload = {
        title: $("title").value.trim(),
        description: $("description").value.trim(),
        project: $("project").value.trim(),
        severity: $("severity").value,
        assigned_to: $("assigned-to").value.trim()
    };

    try {
        if (activeBugId) {
            await request(`/api/bugs/${activeBugId}`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });

            toast("Issue updated");

        } else {
            await request("/api/bugs", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            toast("Issue created");
        }

        closeModal(issueModal);

        setTimeout(() => {
            location.reload();
        }, 300);

    } catch (error) {
        toast(error.message);
    }
});


/* Dashboard buttons */

document.addEventListener("click", async event => {

    const closeButton = event.target.closest("[data-close]");

    if (closeButton) {
        closeModal(issueModal);
        closeModal(detailModal);
        return;
    }

    if (event.target === issueModal) {
        closeModal(issueModal);
    }

    if (event.target === detailModal) {
        closeModal(detailModal);
    }

    if (
        event.target.closest("#open-create") ||
        event.target.closest("#empty-create")
    ) {
        openCreate();
        return;
    }

    const action = event.target.closest("[data-action]");

    if (!action) {
        return;
    }

    const row = action.closest("tr[data-id]");

    if (!row) {
        return;
    }

    const id = row.dataset.id;

    /* View issue */

    if (action.dataset.action === "view") {
        await showDetails(id);
    }

    /* Edit issue */

    if (action.dataset.action === "edit") {
        try {
            const bug = await loadBug(id);

            fillForm(bug);

        } catch (error) {
            toast(error.message);
        }
    }

    /* Delete issue */

    if (action.dataset.action === "delete") {

        const confirmed = confirm(
            `Delete issue #${id}? This also removes its comments and activity history.`
        );

        if (!confirmed) {
            return;
        }

        try {
            await request(`/api/bugs/${id}`, {
                method: "DELETE"
            });

            toast("Issue deleted");

            setTimeout(() => {
                location.reload();
            }, 300);

        } catch (error) {
            toast(error.message);
        }
    }
});


/* Update status directly from the table */

document.addEventListener("change", async event => {

    if (!event.target.matches('[data-action="status"]')) {
        return;
    }

    const row = event.target.closest("tr[data-id]");

    try {
        await request(
            `/api/bugs/${row.dataset.id}/status`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    status: event.target.value
                })
            }
        );

        toast("Status updated");

        setTimeout(() => {
            location.reload();
        }, 300);

    } catch (error) {
        toast(error.message);
    }
});


/* Close modals using Escape */

document.addEventListener("keydown", event => {

    if (event.key === "Escape") {
        closeModal(issueModal);
        closeModal(detailModal);
    }

});