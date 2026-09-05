// ==========================================
// START VALIDATION
// ==========================================

function showValidator() {
    document.getElementById("validator").scrollIntoView({
        behavior: "smooth"
    });

    document.getElementById("organisation").focus();
}


// ==========================================
// FORM SUBMISSION
// ==========================================

document
    .getElementById("validationForm")
    .addEventListener("submit", async function (event) {

        event.preventDefault();

        const validateButton =
            document.querySelector(".validate-btn");

        const resultContent =
            document.getElementById("resultContent");


        // ==========================================
        // COLLECT FORM DATA
        // ==========================================

        const data = {
            organisation: document.getElementById("organisation").value.trim(),
            partner: document.getElementById("partner").value.trim(),
            field_name: document.getElementById("field_name").value.trim(),
            sample_value: document.getElementById("sample_value").value.trim(),
            expected_type: document.getElementById("expected_type").value.trim(),
            expected_masking: document.getElementById("expected_masking").value.trim(),
            access_role: document.getElementById("access_role").value,
            actual_value: document.getElementById("actual_value").value.trim()
        };


        // ==========================================
        // LOADING STATE
        // ==========================================

        validateButton.disabled = true;
        validateButton.innerHTML = "⏳ Validating...";

        resultContent.innerHTML = `
            <div class="empty-result">
                <div class="empty-icon">⏳</div>
                <h3>Validation in Progress</h3>
                <p>Checking detection, masking and access permissions...</p>
            </div>
        `;


        try {

            // ==========================================
            // SEND DATA TO FASTAPI
            // ==========================================

            const response = await fetch(
                "http://127.0.0.1:8000/validate",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(data)
                }
            );


            // ==========================================
            // HANDLE BACKEND ERROR
            // ==========================================

            if (!response.ok) {
                throw new Error(
                    `Server returned ${response.status}`
                );
            }


            const result = await response.json();


            // ==========================================
            // DETERMINE PUBLICATION STATUS
            // ==========================================

            const isAllowed =
                result.publication === "ALLOW";


            const statusClass =
                isAllowed ? "result-success" : "result-danger";


            const statusIcon =
                isAllowed ? "✅" : "❌";


            const statusText =
                isAllowed
                    ? "ANALYTICS PUBLICATION ALLOWED"
                    : "ANALYTICS PUBLICATION BLOCKED";


            // ==========================================
            // DISPLAY RESULT
            // ==========================================

            resultContent.innerHTML = `

                <div class="validation-status ${statusClass}">

                    <span class="status-large-icon">
                        ${statusIcon}
                    </span>

                    <div>
                        <h3>${statusText}</h3>

                        <p>
                            Security validation completed successfully.
                        </p>
                    </div>

                </div>


                <div class="result-grid">

                    <div class="result-item">
                        <span>Organisation</span>
                        <strong>${escapeHTML(result.organisation)}</strong>
                    </div>

                    <div class="result-item">
                        <span>Partner</span>
                        <strong>${escapeHTML(result.partner)}</strong>
                    </div>

                    <div class="result-item">
                        <span>Field</span>
                        <strong>${escapeHTML(result.field_name)}</strong>
                    </div>

                    <div class="result-item">
                        <span>Detected Type</span>
                        <strong>${escapeHTML(result.detected_type)}</strong>
                    </div>

                    <div class="result-item">
                        <span>Masking Status</span>
                        <strong>${escapeHTML(result.masking_status)}</strong>
                    </div>

                    <div class="result-item">
                        <span>Access Result</span>
                        <strong>${escapeHTML(result.access_result)}</strong>
                    </div>

                </div>


                <div class="final-decision">

                    <span>FINAL PUBLICATION DECISION</span>

                    <strong class="${statusClass}">
                        ${result.publication}
                    </strong>

                </div>

            `;


            // ==========================================
            // SCROLL TO RESULT
            // ==========================================

            document
                .getElementById("result")
                .scrollIntoView({
                    behavior: "smooth"
                });


        } catch (error) {

            // ==========================================
            // CONNECTION ERROR
            // ==========================================

            resultContent.innerHTML = `

                <div class="validation-status result-danger">

                    <span class="status-large-icon">
                        ⚠️
                    </span>

                    <div>

                        <h3>Backend Connection Failed</h3>

                        <p>
                            Unable to connect to the validation server.
                        </p>

                    </div>

                </div>

                <div class="error-help">

                    <strong>What to check:</strong>

                    <p>
                        Make sure FastAPI is running at
                        <code>http://127.0.0.1:8000</code>
                    </p>

                </div>

            `;

            console.error("Validation Error:", error);

        } finally {

            // ==========================================
            // RESET BUTTON
            // ==========================================

            validateButton.disabled = false;
            validateButton.innerHTML = "🔍 Validate Field";

        }

    });


// ==========================================
// HTML SECURITY
// Prevent HTML / XSS injection
// ==========================================

function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}