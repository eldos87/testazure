import streamlit as st
import pandas as pd
import base64
import sqlite3
import random
from datetime import datetime  # Import datetime module


st.set_page_config(page_title="Test review")
# Custom CSS to add background color, highlight box, and center image
st.markdown(
    """
    <style>
    .stApp {
        background-color: #b1dee9;
    }
    .highlight-box {
        border: 2px solid;
        padding: 10px;
        margin: 10px 0;
        background-color: #FFFFFF;
        border-radius: 5px;
    }
    .centered-image {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 25%;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Initialize database connection
conn = sqlite3.connect('ratings.db', check_same_thread=False)
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS ratings (
    item TEXT PRIMARY KEY,
    description TEXT,
    rating TEXT,
    timestamp TEXT
)
''')

# Function to insert/update rating with timestamp
def insert_rating(item, description, rating):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
    c.execute('''
    INSERT INTO ratings (item, description, rating, timestamp)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(item) DO UPDATE SET rating=excluded.rating, timestamp=excluded.timestamp
    ''', (item, description, rating, timestamp))
    conn.commit()

# Function to retrieve ratings from the database
def fetch_ratings():
    c.execute("SELECT * FROM ratings")
    return c.fetchall()

# Function to get rated items from the database
def get_rated_items():
    c.execute("SELECT item FROM ratings")
    return {row[0] for row in c.fetchall()}

# Function to convert dataframe to CSV for download
def convert_df(df):
    return df.to_csv().encode('utf-8')

# Function to decode base64 image and display it in Streamlit with reduced size
def display_image(base64_str, caption, width=300):  # Adjust the width as needed
    image_data = base64.b64decode(base64_str)
    st.image(image_data, caption=caption, width=width)

# Streamlit App
st.title("SEO Content Review")
st.write("---")

# Read CSV from local
csv_path = 'data.csv'  # Replace with your actual CSV file path

# Initialize session state variables
if 'current_rating' not in st.session_state:
    st.session_state.current_rating = None  # Initialize current rating to None
if 'current_record_index' not in st.session_state:
    st.session_state.current_record_index = 0  # Initialize current record index
if 'rated' not in st.session_state:
    st.session_state.rated = 0   # Initialize rated
if 'skipped' not in st.session_state:
    st.session_state.skipped = 0   # Initialize skipped


try:
    df = pd.read_csv(csv_path)

    # Get rated items from the database
    rated_items = get_rated_items()

    available_records = df[~df['item'].isin(rated_items)]
    
    if (available_records.empty) | (st.session_state.current_record_index==2):
        st.write("#### Selected records have been rated. Thank you!")

        # Fetch data from SQLite and display in the app
        ratings = fetch_ratings()
        rating_df = pd.DataFrame(ratings, columns=['item', 'Description', 'Rating', 'Timestamp'])
        
        st.write(f"**Total Rated Records:** {st.session_state.rated}")
        st.write(f"**Total Skipped Records:** {st.session_state.skipped}")
        st.dataframe(rating_df)
        
        # Download button for SQLite data
        csv = convert_df(rating_df)
        st.download_button(
            label="Download Ratings as CSV",
            data=csv,
            file_name='ratings.csv',
            mime='text/csv',
        )

    else:
        if st.session_state.current_record_index >= len(available_records):
            # Reset current record index and select new records
            st.session_state.current_record_index = 0
            selected_records = random.sample(available_records.to_dict('records'), min(2, len(available_records)))

        # Load the current record to display
        current_record = available_records.iloc[st.session_state.current_record_index]
        image_base64 = current_record['image']
        item = current_record['item']
        description = current_record['description']

        # Display Image with reduced size
        display_image(base64_str=image_base64, caption=item, width=300)
        
        # Show item and Description
        st.write(f"**Item:** {item}")
        st.write(f"**Description:** {description}")

        # Thumbs up and down buttons for rating
        st.write("")
        st.write("")
        st.write(" #### Please select your rating or skip")
        col1, col2 = st.columns(2)
        with col1:
            thumbs_up = st.button('Good 👍 ', key='thumbs_up')
        with col2:
            thumbs_down = st.button('Bad 👎', key='thumbs_down')

        # Set the rating based on the button clicked
        if thumbs_up:
            st.session_state.current_rating = 'Good'
        elif thumbs_down:
            st.session_state.current_rating = 'Bad'

        if st.session_state.current_rating is not None:
            if st.button("Submit"):
                # Log the rating with timestamp
                insert_rating(item, description, st.session_state.current_rating)
                
                # Reset the rating state
                st.session_state.current_rating = None
                
                # Move to the next record
                st.session_state.current_record_index += 1
                
                # increment rated count
                st.session_state.rated +=1

                # Trigger UI refresh
                st.rerun()
        else:
            if st.button("Skip"):
                # Skip to the next record without logging any rating
                st.session_state.current_record_index += 1

                # increment skipped count
                st.session_state.skipped +=1

                # Trigger UI refresh
                st.rerun()

        # Show rated and skipped records
        st.write("")
        st.write("")
        st.write(f"Rated Records: {st.session_state.rated}")
        st.write(f"Skipped Records: {st.session_state.skipped}")

except FileNotFoundError:
    st.error(f"The file at path `{csv_path}` was not found. Please check the file path.")



