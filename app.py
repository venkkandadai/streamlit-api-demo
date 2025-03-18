import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Base URL for API
BASE_URL = "https://flask-api-render-0vqx.onrender.com/api"

# ✅ Function to fetch data from API (with caching)
@st.cache_data
def fetch_data(endpoint, params):
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
        return None

# ✅ Function to fetch test IDs dynamically
@st.cache_data
def get_test_ids():
    test_data = fetch_data("tests", {})  # Fetch test IDs from API
    if isinstance(test_data, list):  
        return [test["test_id"] for test in test_data if "test_id" in test]  # Extract test IDs
    return []  # Return empty list if fetch fails

# Page 1 ✅ Main function for Basic Functionality
def basic_functionality():
    st.title("📡 NBME API - Basic Functionality")

    # User API Key input
    api_key = st.text_input("🔑 Enter your API Key:", type="password")

    # Fetch test list
    test_ids = get_test_ids()  # Get test IDs dynamically

    # Endpoint Selection
    endpoint_options = {
        "/exam-stats": "exam-stats",
        "/tests": "tests",
        "/students/tests": "students/tests",
        "/students": "students",
        "/students/scores": "students/scores",
        "/students/scores/details": "students/scores/details",
        "/students/usmle-results": "students/usmle-results"
    }
    
    selected_endpoint = st.selectbox("📌 Choose an endpoint:", list(endpoint_options.keys()))

    # Check if using the Master Key
    MASTER_API_KEY = "a71ed21d7da1aead4e5088827d1c67fc"
    school_id = None  # Initialize school_id

    if api_key:
        if api_key == MASTER_API_KEY:
            school_id = st.selectbox("🏥 Select School ID:", ["MedSchoolA", "MedSchoolB", "MedSchoolC", "MedSchoolD"])
        else:
            school_map = {
                "003fb7e922cd6595f4243703b7d3a32f": "MedSchoolA",
                "2d7ebd0c14a5c41d18172341920cd222": "MedSchoolB",
                "9198340729aae63e06785df4cd61d8b2": "MedSchoolC",
                "20e8b4cad8f774a7bbe076029ba3a38c": "MedSchoolD",
            }
            school_id = school_map.get(api_key)

            if school_id:
                st.success(f"✅ API Key is valid for {school_id}.")
            else:
                st.error("❌ Invalid API Key or unauthorized access.")
                return  # Stop execution if API key is incorrect

    # Initialize params dictionary
    params = {"api_key": api_key}

    # Dynamic input fields based on endpoint, ensuring batching where applicable
    if selected_endpoint in ["/students/tests", "/students", "/students/scores", "/students/scores/details", "/students/usmle-results"]:
        params["school_id"] = school_id  # Add school_id when required

        # Allow batching on student_id for applicable endpoints
        if selected_endpoint in ["/students/tests", "/students", "/students/usmle-results"]:
            student_id_list = st.text_area("Enter Student IDs (comma-separated):")
            if student_id_list:
                student_ids = [id.strip() for id in student_id_list.split(",") if id.strip().isdigit()]
                if student_ids:
                    params["student_id"] = ",".join(student_ids)  # Batch multiple student IDs
                else:
                    st.warning("Please enter valid student IDs.")

        elif selected_endpoint in ["/students/scores", "/students/scores/details"]:
            student_id_list = st.text_area("Enter Student IDs (comma-separated):")
            if student_id_list:
                student_ids = [id.strip() for id in student_id_list.split(",") if id.strip().isdigit()]
                if student_ids:
                    params["student_id"] = ",".join(student_ids)  # Batch multiple student IDs
                else:
                    st.warning("Please enter valid student IDs.")

            # ✅ Enable test_id batching using multiselect dropdown
            if test_ids:
                selected_test_ids = st.multiselect("📝 Select Test ID(s):", test_ids)
                if selected_test_ids:
                    params["test_id"] = ",".join(selected_test_ids)  # Batch multiple test IDs
            else:
                st.error("❌ Could not fetch available test IDs. Please check your API connection.")

    if st.button("🚀 Fetch Data"):
        st.write(f"📌 API Request: `{BASE_URL}/{endpoint_options[selected_endpoint]}`")
        st.write(f"🔍 Parameters Sent: `{params}`")  

        data = fetch_data(endpoint_options[selected_endpoint], params)

        if data:
            st.subheader("📊 API Response:")
            st.json(data)  # Display raw JSON response

            # Ensure the response is a list before converting to a DataFrame
            if isinstance(data, dict):
                data = [data]  # Convert single dictionary into a list of dictionaries
            elif isinstance(data, str):
                st.error(f"Unexpected API response: {data}")
                return

            # Convert to DataFrame
            df = pd.DataFrame(data)
            st.dataframe(df)


# Page 2: Generate Dataset and Identify At-Risk Students
def generate_dataset():
    st.title("📊 Generate At-Risk Dataset for Comprehensive Basic Sciences Subject Exam")

    api_key = st.text_input("🔑 Enter your API Key:", type="password")
    school_id = st.selectbox("🏥 Select School ID:", ["MedSchoolA", "MedSchoolB", "MedSchoolC", "MedSchoolD"])

    if not api_key:
        st.warning("Please enter your API key to proceed.")
        return

    if st.button("🚀 Generate Dataset"):
        with st.spinner("Fetching data..."):

            # ✅ Fetch Student Roster (SINGLE API CALL)
            roster_params = {"api_key": api_key, "school_id": school_id}
            roster = fetch_data("students", roster_params)

            if not isinstance(roster, list):
                st.error(f"Unexpected response from API: {roster}")
                return  # Stop execution if data is not a list

            # ✅ Extract all student IDs for batch request
            student_ids = [student["student_id"] for student in roster]

            # ✅ Fetch SE-1 Scores in BATCH instead of per student (SINGLE API CALL)
            score_params = {
                "api_key": api_key,
                "school_id": school_id,
                "student_id": ",".join(student_ids),  # Batch request
                "test_id": "SE-1"  # Only fetching SE-1 scores
            }
            scores_data = fetch_data("students/scores", score_params)

            # ✅ Ensure scores are in a usable format
            scores = []
            if isinstance(scores_data, list):
                for score_entry in scores_data:
                    scores.append({
                        "student_id": score_entry.get("student_id"),
                        "score": score_entry.get("score", None)
                    })

            # ✅ Fetch National Statistics ONCE (SINGLE API CALL)
            exam_stats = fetch_data("exam-stats", {})
            national_mean = next((stat["mean"] for stat in exam_stats if stat["test_id"] == "SE-1"), None)

            # ✅ Merge Data (Faster Pandas Operations)
            roster_df = pd.DataFrame(roster)
            scores_df = pd.DataFrame(scores)
            merged_df = pd.merge(roster_df, scores_df, on="student_id", how="left")

            # ✅ Add "At-Risk" Column
            if national_mean is not None:
                merged_df["At-Risk"] = merged_df["score"] < national_mean
            else:
                st.error("Could not retrieve national mean for SE-1.")

            # ✅ Display Data
            st.subheader("📋 Generated Dataset")
            st.dataframe(merged_df)

            # ✅ Downloadable CSV
            csv = merged_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Dataset as CSV", data=csv, file_name="at_risk_students.csv", mime="text/csv")

            # ✅ Visualization - SE-1 Score Distribution
            st.subheader("📈 SE-1 Score Distribution")
            fig, ax = plt.subplots()
            ax.hist(merged_df["score"].dropna(), bins=20, edgecolor="black", alpha=0.7)
            ax.axvline(national_mean, color="red", linestyle="dashed", label=f"National Mean: {national_mean}")
            ax.set_xlabel("SE-1 Score")
            ax.set_ylabel("Frequency")
            ax.set_title("SE-1 Score Distribution")
            ax.legend()
            st.pyplot(fig)

# Streamlit Navigation
st.sidebar.title("🔀 Navigation")
page = st.sidebar.radio("Go to", ["Basic Functionality", "Generate Dataset"])

if page == "Basic Functionality":
    basic_functionality()
else:
    generate_dataset()



