import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px


def create_connection():
    return mysql.connector.connect(
        host="localhost",   
        user="root",        
        password="",       
        database="test"    
        
    )

# Execute query and fetch data
def run_query(query):
    try:
        conn = create_connection()
        data = pd.read_sql(query, conn)
        conn.close()
        return data
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# App title
st.title("Allwyn Book Store Analysis")

# Sidebar navigation
menu = st.sidebar.selectbox("Select Analysis", [
    "Overview",
    "Availability of eBooks vs Physical Books",
    "Publisher Statistics",
    "Top Books Analysis",
    "Books Published After 2010",
    "Discount Analysis",
    "Average Page Count",
    "Author Statistics",
    "Books with Specific Criteria",
    "Outliers and Trends",
    "Custom Query"
])

if menu == "Overview":
    st.subheader("Overview")
    st.markdown("""
        Welcome to the Book Analysis Dashboard. Use the sidebar to explore various analyses:
        - Book availability and trends
        - Publisher statistics
        - Top-rated and expensive books
        - Outliers and custom queries
    """)

elif menu == "Availability of eBooks vs Physical Books":
    st.subheader("Availability of eBooks vs Physical Books")
    query = '''SELECT CASE WHEN
    nvl(t1.isEbook, 'False') ='False' THEN 'Physical Book' ELSE 'Ebook'
END AS book_format,
COUNT(*) AS total_books
FROM
    life_new1 t1
GROUP BY
    isEbook;'''
    data = run_query(query)
    if not data.empty:
        fig = px.pie(data, names="book_format", values="total_books", title="Book Formats Distribution")
        st.plotly_chart(fig)

elif menu == "Publisher Statistics":
    st.subheader("Publisher Statistics")
    option = st.radio("Select Option", ["Most Books Published", "Highest Average Rating"])
    if option == "Most Books Published":
        query = """ SELECT l1.publisher as  publisher, count(*) as cnt
        FROM life_new1 l1
        GROUP BY publisher        
        ORDER BY cnt  DESC
        LIMIT 10
        
        """
    else:
        query = """
        SELECT l1.publisher as  publisher, round( AVG(l1.averageRating),2) AS avg_rating
        FROM life_new1 l1
        GROUP BY publisher
        HAVING COUNT(*) > 10
        ORDER BY avg_rating DESC
        LIMIT 10;
        """
    data = run_query(query)
    if not data.empty:
        st.bar_chart(data.set_index("publisher"))

elif menu == "Top Books Analysis":
    st.subheader("Top 5 Most Expensive Books")
    query = "SELECT dr.book_title as title, dr.amount_retailPrice as retail_price FROM life_new1  dr ORDER BY retail_price DESC LIMIT 5;"
    data = run_query(query)
    if not data.empty:
        st.table(data)

elif menu == "Books Published After 2010":
    st.subheader("Books Published After 2010 with 500+ Pages")
    query = """
    SELECT dr.book_title as title, dr.pageCount as page_count, dr.year as publication_year
    FROM life_new1 as dr
    WHERE year > 2010 AND pageCount >= 500;
    """
    data = run_query(query)
    if not data.empty:
        st.dataframe(data)

elif menu == "Discount Analysis":
    st.subheader("Books with Discounts Greater than 20%")
    query = """
    SELECT t.book_title as title, t.amount_listPrice as retail_price, amount_retailPrice as  discount_price,
          ROUND((t.amount_listPrice - amount_retailPrice) /  amount_listPrice * 100, 2) AS discount_percentage
    FROM life_new1 as t
    where amount_retailPrice>0 and amount_listPrice >amount_retailPrice
   and   ROUND((amount_listPrice - amount_retailPrice) / amount_listPrice * 100, 2)>0.2
    """
    data = run_query(query)
    if not data.empty:
        fig = px.bar(data, x="title", y=["retail_price", "discount_price"], barmode="group", title="Discounted Books")
        st.plotly_chart(fig)

elif menu == "Average Page Count":
    st.subheader("Average Page Count")
    option = st.radio("Select Option", ["eBooks vs Physical Books", "By Category"])
    if option == "eBooks vs Physical Books":
        query = """
        SELECT CASE WHEN
    nvl(l1.isEbook, 'False') = 'False' THEN 'Ebook' ELSE 'Physical Book'
END AS book_format,
round(AVG(l1.pageCount),2) AS avg_page_count
FROM
    life_new1 l1
GROUP BY isEbook;
        """
    else:
        query = """
        SELECT
    l1.categories,
   round( AVG(l1.pageCount),2) AS avg_page_count
FROM
    life_new1 l1
GROUP BY
    categories;
        """
    data = run_query(query)
    if not data.empty:
        fig = px.bar(data, x=data.columns[0], y="avg_page_count", title="Average Page Count")
        st.plotly_chart(fig)

elif menu == "Author Statistics":
    st.subheader("Top Authors")
    query = """
    SELECT nvl(l1.book_authors,'unknown') as author, COUNT(*) AS total_books 
    FROM life_new1 l1
    GROUP BY l1.book_authors
    ORDER BY total_books DESC
    LIMIT 10;
    """
    data = run_query(query)
    if not data.empty:
        fig = px.bar(data, x="author", y="total_books", title="Top Authors by Book Count")
        st.plotly_chart(fig)

elif menu == "Books with Specific Criteria":
    st.subheader("Filter Books by Criteria")
    criteria = st.text_input("Enter keyword to search in titles:")
    if criteria:
        query = f"""
        SELECT l1.book_title, nvl(l1.amount_retailPrice, l1.amount_listPrice)
        FROM life_new1 l1
        WHERE book_title LIKE '%{criteria}%';
        """
        data = run_query(query)
        if not data.empty:
            st.table(data)

elif menu == "Outliers and Trends":
    st.subheader("Books with Outlier Ratings")
    query = """
    WITH stats AS (
        SELECT AVG(averageRating) AS avg_rating, STDDEV(averageRating) AS stddev_rating
        FROM life_new1 l1
    )
    SELECT l1.book_title as title, averageRating as average_rating,  l1.ratingsCount as ratings_count
    FROM life_new1 l1, stats
    WHERE averageRating > avg_rating + 2 * stddev_rating
       OR averageRating < avg_rating - 2 * stddev_rating;
    """
    data = run_query(query)
    if not data.empty:
        fig = px.scatter(data, x="ratings_count", y="average_rating", title="Outlier Books", hover_data=["title"])
        st.plotly_chart(fig)

elif menu == "Custom Query":
    st.subheader("Run Your Custom Query")
    user_query = st.text_area("Enter SQL Query(table name : life_new1):")
    if user_query:
        try:
            data = run_query(user_query)
            if not data.empty:
                st.dataframe(data)
        except Exception as e:
            st.error(f"Error: {e}")
