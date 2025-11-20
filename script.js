document.addEventListener("DOMContentLoaded", function () {

    const runBtn = document.getElementById("runBtn");
    const btnText = document.getElementById("btnText");
    const spinner = document.getElementById("spinner");
    const progressBar = document.getElementById("progressBar");
    const status = document.getElementById("status");

    runBtn.addEventListener("click", async () => {

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            status.textContent = "❌ Enter username and password.";
            return;
        }

        // UI START
        runBtn.disabled = true;
        spinner.classList.remove("hidden");
        btnText.textContent = "Running...";
        progressBar.classList.remove("hidden");
        status.textContent = "";

        try {
            // Step 1 — Open login page
            const win = window.open("http://webprosindia.com/Gokaraju/", "_blank");

            if (!win) {
                status.textContent = "❌ Allow pop-ups to use automation!";
                resetUI();
                return;
            }

            await waitFor(() => win.document.getElementById("txtId2"), 8000);
            win.document.getElementById("txtId2").value = username;
            win.document.getElementById("txtPwd2").value = password;
            win.document.getElementById("imgBtn2").click();

            // Step 2 — Wait for FEEDBACK button
            await waitFor(() => win.document.querySelector("a[href*='StudentFeedback']") ||
                win.document.querySelector("a:contains('FEEDBACK')"), 8000);

            win.document.querySelector("a[href*='StudentFeedback'], a:contains('FEEDBACK')").click();

            // Step 3 — Wait for iframe
            await waitFor(() => win.document.getElementsByName("capIframe")[0], 8000);

            const iframe = win.document.getElementsByName("capIframe")[0];
            const frameDoc = iframe.contentWindow.document;

            // Step 4 — Select term automatically
            await waitFor(() => frameDoc.getElementById("ctl00_CapPlaceHolder_ddlExams"), 5000);
            frameDoc.getElementById("ctl00_CapPlaceHolder_ddlExams").value = "1";

            // Step 5 — Fill all text inputs with 4
            await waitFor(() => frameDoc.querySelectorAll("input[type='text'][maxlength='1']").length > 0, 5000);

            const inputs = frameDoc.querySelectorAll("input[type='text'][maxlength='1']");
            inputs.forEach(el => el.value = "4");

            // Step 6 — Click submit
            const submitBtn = frameDoc.getElementById("btnfbsave");
            submitBtn.click();

            // Step 7 — Accept popup
            await new Promise(res => setTimeout(res, 1000)); // wait for popup
            try {
                win.alert = function () { return true; };
                win.confirm = function () { return true; };
            } catch { }

            status.textContent = "✅ Feedback submitted successfully!";

        } catch (err) {
            status.textContent = "❌ Failed: " + err;
        }

        resetUI();
    });

    // Utility: wait for condition
    function waitFor(check, timeout) {
        return new Promise((resolve, reject) => {
            const start = Date.now();
            const timer = setInterval(() => {
                if (check()) {
                    clearInterval(timer);
                    resolve();
                }
                if (Date.now() - start > timeout) {
                    clearInterval(timer);
                    reject("Timeout");
                }
            }, 100);
        });
    }

    function resetUI() {
        btnText.textContent = "Fill Feedback";
        spinner.classList.add("hidden");
        progressBar.classList.add("hidden");
        runBtn.disabled = false;
    }
});
