from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


app = FastAPI(
    title="Sensitive Data Validator API"
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST FORMAT
# ============================================================

class ValidationRequest(BaseModel):

    organisation: str
    partner: str
    field_name: str
    sample_value: str
    expected_type: str
    expected_masking: str
    access_role: str
    actual_value: str


# ============================================================
# SENSITIVE FIELD DETECTION
# ============================================================

def detect_field(field_name, sample_value):

    field = field_name.lower()
    value = str(sample_value)

    # Field name based detection

    if any(x in field for x in ["email", "mail"]):
        return "Email"

    if any(x in field for x in ["phone", "mobile"]):
        return "Phone"

    if any(x in field for x in ["card", "cc"]):
        return "Card"

    if any(x in field for x in ["name", "nm"]):
        return "Name"

    # Value pattern based detection

    if "@" in value:
        return "Email"

    if value.isdigit() and len(value) == 10:
        return "Phone"

    if value.isdigit() and len(value) == 16:
        return "Card"

    return "Normal"


# ============================================================
# MASKING CHECK
# ============================================================

def check_masking(expected_mask, actual_value):

    if expected_mask.lower() == "none":
        return "Not Required"

    if expected_mask == actual_value:
        return "Protected"

    return "Not Protected"


# ============================================================
# ACCESS POLICY
# ============================================================

permissions = {

    "Admin": {
        "Email": "FULL",
        "Phone": "FULL",
        "Card": "FULL",
        "Name": "FULL",
        "Normal": "FULL"
    },

    "Manager": {
        "Email": "MASKED",
        "Phone": "MASKED",
        "Card": "MASKED",
        "Name": "MASKED",
        "Normal": "FULL"
    },

    "Analyst": {
        "Email": "MASKED",
        "Phone": "MASKED",
        "Card": "MASKED",
        "Name": "MASKED",
        "Normal": "FULL"
    }
}


def check_access(role, field_type, actual_value):

    permission = permissions.get(
        role,
        {}
    ).get(
        field_type,
        "DENIED"
    )

    if permission == "DENIED":
        return "ACCESS DENIED"

    if permission == "FULL":
        return "FULL ACCESS"

    if permission == "MASKED":

        if "*" in actual_value:
            return "MASKED ACCESS"

        return "ACCESS DENIED"

    return "ACCESS DENIED"


# ============================================================
# HOME API
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Sensitive Data Validator API is running"
    }


# ============================================================
# JSON VALIDATION API
# ============================================================

@app.post("/validate")
def validate_data(request: ValidationRequest):

    detected_type = detect_field(
        request.field_name,
        request.sample_value
    )

    masking_status = check_masking(
        request.expected_masking,
        request.actual_value
    )

    access_result = check_access(
        request.access_role,
        detected_type,
        request.actual_value
    )

    if (
        masking_status == "Not Protected"
        or access_result == "ACCESS DENIED"
    ):

        publication = "BLOCK"

    else:

        publication = "ALLOW"

    return {

        "organisation": request.organisation,

        "partner": request.partner,

        "field_name": request.field_name,

        "detected_type": detected_type,

        "masking_status": masking_status,

        "access_result": access_result,

        "publication": publication

    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    return """

    <html>

    <head>

        <title>Security Dashboard</title>

        <style>

            body {
                font-family: Arial;
                margin: 40px;
                background: #f4f6f8;
            }

            h1 {
                text-align: center;
                margin-bottom: 10px;
            }

            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }

            .container {
                display: flex;
                gap: 20px;
                justify-content: center;
                margin-top: 25px;
                flex-wrap: wrap;
            }

            .card {
                background: white;
                padding: 25px;
                width: 180px;
                text-align: center;
                border-radius: 10px;
                box-shadow: 0 2px 8px #ccc;
            }

            .number {
                font-size: 30px;
                font-weight: bold;
                margin-top: 8px;
            }

            .blocked {
                margin: 40px auto;
                background: #ffe5e5;
                padding: 25px;
                max-width: 700px;
                text-align: center;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
                color: red;
            }

            .section-title {
                text-align: center;
                margin-top: 45px;
                margin-bottom: 15px;
            }

            .table-container {
                overflow-x: auto;
                margin: 20px auto;
                max-width: 1100px;
            }

            table {
                width: 100%;
                background: white;
                border-collapse: collapse;
                box-shadow: 0 2px 8px #ccc;
            }

            th {
                background: #222;
                color: white;
                padding: 14px;
            }

            td {
                padding: 12px;
                border: 1px solid #ddd;
                text-align: center;
            }

            .protected {
                color: green;
                font-weight: bold;
            }

            .not-protected {
                color: red;
                font-weight: bold;
            }

            .masked-access {
                color: green;
                font-weight: bold;
            }

            .denied {
                color: red;
                font-weight: bold;
            }

            .allow {
                color: green;
                font-weight: bold;
            }

            .block {
                color: red;
                font-weight: bold;
            }

            .metric-table {
                max-width: 600px;
                margin: 30px auto;
            }

            .form-box {
                max-width: 650px;
                margin: 20px auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 8px #ccc;
            }

            input,
            select {
                width: 100%;
                padding: 10px;
                margin: 8px 0 15px;
                box-sizing: border-box;
            }

            button {
                width: 100%;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }

        </style>

    </head>


    <body>


        <h1>🔐 Sensitive Data Security Dashboard</h1>


        <div class="subtitle">

            Sensitive Data Detection, Masking & Access Validation

        </div>


        <!-- ================================================= -->
        <!-- DETECTION METRICS -->
        <!-- ================================================= -->

        <div class="container">

            <div class="card">

                <div>Baseline Accuracy</div>

                <div class="number">87.5%</div>

            </div>


            <div class="card">

                <div>Hybrid Accuracy</div>

                <div class="number">100%</div>

            </div>


            <div class="card">

                <div>Improvement</div>

                <div class="number">+12.5%</div>

            </div>

        </div>


        <!-- ================================================= -->
        <!-- SECURITY METRICS -->
        <!-- ================================================= -->

        <div class="container">

            <div class="card">

                <div>Sensitive Fields</div>

                <div class="number">8</div>

            </div>


            <div class="card">

                <div>Protected</div>

                <div class="number">5</div>

            </div>


            <div class="card">

                <div>Masking Failures</div>

                <div class="number">3</div>

            </div>


            <div class="card">

                <div>Access Denied</div>

                <div class="number">3</div>

            </div>

        </div>


        <!-- ================================================= -->
        <!-- FINAL DECISION -->
        <!-- ================================================= -->

        <div class="blocked">

            ❌ ANALYTICS PUBLICATION BLOCKED

            <br>

            <small>

                Sensitive data protection policy violated.

            </small>

        </div>


        <!-- ================================================= -->
        <!-- METRIC SUMMARY -->
        <!-- ================================================= -->

        <h2 class="section-title">

            📊 Security Metrics

        </h2>


        <table class="metric-table">

            <tr>

                <th>Metric</th>

                <th>Result</th>

            </tr>


            <tr>

                <td>Total Fields</td>

                <td>9</td>

            </tr>


            <tr>

                <td>Sensitive Fields</td>

                <td>8</td>

            </tr>


            <tr>

                <td>Protected Fields</td>

                <td>5</td>

            </tr>


            <tr>

                <td>Masking Failures</td>

                <td>3</td>

            </tr>


            <tr>

                <td>Access Denied</td>

                <td>3</td>

            </tr>


            <tr>

                <td>Allowed</td>

                <td>5</td>

            </tr>


            <tr>

                <td>Blocked</td>

                <td>4</td>

            </tr>


            <tr>

                <td>Protection Rate</td>

                <td>62.50%</td>

            </tr>

        </table>


        <!-- ================================================= -->
        <!-- FIELD VALIDATION DETAILS -->
        <!-- ================================================= -->

        <h2 class="section-title">

            🔍 Field Validation Details

        </h2>


        <div class="table-container">

        <table>

            <tr>

                <th>Organisation</th>

                <th>Partner</th>

                <th>Field</th>

                <th>Type</th>

                <th>Masking</th>

                <th>Access</th>

                <th>Final</th>

            </tr>


            <tr>

                <td>FinA</td>

                <td>PayX</td>

                <td>email</td>

                <td>Email</td>

                <td class="protected">

                    Protected

                </td>

                <td class="masked-access">

                    MASKED ACCESS

                </td>

                <td class="allow">

                    ALLOW

                </td>

            </tr>


            <tr>

                <td>FinA</td>

                <td>PayX</td>

                <td>phone</td>

                <td>Phone</td>

                <td class="not-protected">

                    Not Protected

                </td>

                <td class="denied">

                    ACCESS DENIED

                </td>

                <td class="block">

                    BLOCK

                </td>

            </tr>


            <tr>

                <td>FinA</td>

                <td>PayX</td>

                <td>card_number</td>

                <td>Card</td>

                <td class="not-protected">

                    Not Protected

                </td>

                <td class="denied">

                    ACCESS DENIED

                </td>

                <td class="block">

                    BLOCK

                </td>

            </tr>


            <tr>

                <td>FinA</td>

                <td>PayX</td>

                <td>amount</td>

                <td>Normal</td>

                <td>

                    Not Required

                </td>

                <td>

                    FULL ACCESS

                </td>

                <td class="allow">

                    ALLOW

                </td>

            </tr>


            <tr>

                <td>FinB</td>

                <td>PayY</td>

                <td>cust_mail</td>

                <td>Email</td>

                <td class="protected">

                    Protected

                </td>

                <td class="masked-access">

                    MASKED ACCESS

                </td>

                <td class="allow">

                    ALLOW

                </td>

            </tr>


            <tr>

                <td>FinB</td>

                <td>PayY</td>

                <td>mobile_no</td>

                <td>Phone</td>

                <td class="protected">

                    Protected

                </td>

                <td class="masked-access">

                    MASKED ACCESS

                </td>

                <td class="allow">

                    ALLOW

                </td>

            </tr>


            <tr>

                <td>FinB</td>

                <td>PayY</td>

                <td>cc_no</td>

                <td>Card</td>

                <td class="protected">

                    Protected

                </td>

                <td class="masked-access">

                    MASKED ACCESS

                </td>

                <td class="allow">

                    ALLOW

                </td>

            </tr>


            <tr>

                <td>FinC</td>

                <td>PayZ</td>

                <td>cust_nm</td>

                <td>Name</td>

                <td class="not-protected">

                    Not Protected

                </td>

                <td>

                    FULL ACCESS

                </td>

                <td class="block">

                    BLOCK

                </td>

            </tr>


            <tr>

                <td>FinC</td>

                <td>PayZ</td>

                <td>customer_email</td>

                <td>Email</td>

                <td class="protected">

                    Protected

                </td>

                <td class="denied">

                    ACCESS DENIED

                </td>

                <td class="block">

                    BLOCK

                </td>

            </tr>

        </table>

        </div>


        <!-- ================================================= -->
        <!-- TEST NEW FIELD -->
        <!-- ================================================= -->

        <h2 class="section-title">

            🧪 Test New Field

        </h2>


        <div class="form-box">

            <form action="/validate-form" method="post">


                <label>Organisation</label>

                <input
                    type="text"
                    name="organisation"
                    value="FinA"
                >


                <label>Partner</label>

                <input
                    type="text"
                    name="partner"
                    value="PayX"
                >


                <label>Field Name</label>

                <input
                    type="text"
                    name="field_name"
                    placeholder="Example: card_number"
                    required
                >


                <label>Sample Value</label>

                <input
                    type="text"
                    name="sample_value"
                    placeholder="Example: 4532123412345678"
                    required
                >


                <label>Expected Type</label>

                <select name="expected_type">

                    <option>Email</option>

                    <option>Phone</option>

                    <option>Card</option>

                    <option>Name</option>

                    <option>Normal</option>

                </select>


                <label>Expected Masking</label>

                <input
                    type="text"
                    name="expected_masking"
                    placeholder="Example: ************5678"
                    required
                >


                <label>Access Role</label>

                <select name="access_role">

                    <option>Analyst</option>

                    <option>Manager</option>

                    <option>Admin</option>

                </select>


                <label>Actual Value</label>

                <input
                    type="text"
                    name="actual_value"
                    placeholder="Enter actual masked/unmasked value"
                    required
                >


                <button type="submit">

                    🔍 VALIDATE FIELD

                </button>


            </form>

        </div>


    </body>

    </html>

    """


# ============================================================
# FORM VALIDATION
# ============================================================

@app.post("/validate-form", response_class=HTMLResponse)
def validate_form(

    organisation: str = Form(...),

    partner: str = Form(...),

    field_name: str = Form(...),

    sample_value: str = Form(...),

    expected_type: str = Form(...),

    expected_masking: str = Form(...),

    access_role: str = Form(...),

    actual_value: str = Form(...)

):

    # Detect sensitive field

    detected_type = detect_field(
        field_name,
        sample_value
    )


    # Check masking

    masking_status = check_masking(
        expected_masking,
        actual_value
    )


    # Check access

    access_result = check_access(
        access_role,
        detected_type,
        actual_value
    )


    # Publication decision

    if (
        masking_status == "Not Protected"
        or access_result == "ACCESS DENIED"
    ):

        publication = "BLOCK"

    else:

        publication = "ALLOW"


    # Result color

    if publication == "ALLOW":

        final_message = "✅ PUBLICATION ALLOWED"

        final_class = "allow"

    else:

        final_message = "❌ PUBLICATION BLOCKED"

        final_class = "block"


    return f"""

    <html>

    <head>

        <title>Validation Result</title>

        <style>

            body {{

                font-family: Arial;

                background: #f4f6f8;

                margin: 40px;

            }}

            .box {{

                max-width: 650px;

                margin: auto;

                background: white;

                padding: 30px;

                border-radius: 10px;

                box-shadow: 0 2px 8px #ccc;

            }}

            h1 {{

                text-align: center;

            }}

            .result {{

                margin: 15px 0;

                padding: 15px;

                border-bottom: 1px solid #ddd;

            }}

            .allow {{

                color: green;

                font-size: 24px;

                font-weight: bold;

                text-align: center;

                margin-top: 25px;

            }}

            .block {{

                color: red;

                font-size: 24px;

                font-weight: bold;

                text-align: center;

                margin-top: 25px;

            }}

            a {{

                display: block;

                text-align: center;

                margin-top: 25px;

            }}

        </style>

    </head>


    <body>


        <div class="box">


            <h1>🔍 Validation Result</h1>


            <div class="result">

                <b>Organisation:</b>

                {organisation}

            </div>


            <div class="result">

                <b>Partner:</b>

                {partner}

            </div>


            <div class="result">

                <b>Field:</b>

                {field_name}

            </div>


            <div class="result">

                <b>Detected Type:</b>

                {detected_type}

            </div>


            <div class="result">

                <b>Expected Type:</b>

                {expected_type}

            </div>


            <div class="result">

                <b>Masking Status:</b>

                {masking_status}

            </div>


            <div class="result">

                <b>Access Result:</b>

                {access_result}

            </div>


            <div class="result">

                <b>Access Role:</b>

                {access_role}

            </div>


            <div class="{final_class}">

                {final_message}

            </div>


            <a href="/dashboard">

                ← Back to Dashboard

            </a>


        </div>


    </body>

    </html>

    """