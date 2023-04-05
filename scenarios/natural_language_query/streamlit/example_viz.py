import streamlit as st
import random
import pandas as pd
import sys
from analyze import AnalyzeGPT
import openai

tables_structure="""
    - Fact.Order(Order_Key(PK),City_Key(FK),Customer_Key(FK),Stock_Item_Key(FK),Order_Date_Key(FK),Picked_Date_Key(FK),Salesperson_Key(FK),Picker_Key(FK),WWI_Order_ID,WWI_Backorder_ID,Description,Package,Quantity,Unit_Price,Tax_Rate,Total_Excluding_Tax,Tax_Amount,Total_Including_Tax,Lineage_Key)
    - Fact.Purchase(Purchase_Key(PK),Date_Key(FK),Supplier_Key(FK),Stock_Item_Key(FK),WWI_Purchase_Order_ID,Ordered_Outers,Ordered_Quantity,Received_Outers,Package,Is_Order_Finalized,Lineage_Key)
    - Fact.Sale(Sale_Key(PK),City_Key(FK),Customer_Key(FK),Bill_To_Customer_Key(FK),Stock_Item_Key(FK),Invoice_Date_Key(FK),Delivery_Date_Key(FK),Salesperson_Key(FK),WWI_Invoice_ID,Description,Package,Quantity,Unit_Price,Tax_Rate,Total_Excluding_Tax,Tax_Amount,Profit,Total_Including_Tax,Total_Dry_Items,Total_Chiller_Items,Lineage_Key)
    - Dimension.City(City_Key(PK),WWI_City_ID,City,State_Province,Country,Continent,Sales_Territory,Region,Subregion,Location,Latest_Recorded_Population,Valid_From,Valid_To,Lineage_Key)
    - Dimension.Customer(Customer_Key(PK),WWI_Customer_ID,Customer,Bill_To_Customer,Category,Buying_Group,Primary_Contact,Postal_Code,Valid_From,Valid_To,Lineage_Key)
    - Dimension.Date(Date(PK),Day_Number,Day,Month,Short_Month,Calendar_Month_Number,Calendar_Month_Label,Calendar_Year,Calendar_Year_Label,Fiscal_Month_Number,Fiscal_Month_Label,Fiscal_Year,Fiscal_Year_Label,ISO_Week_Number)
    - Dimension.Stock_Item(Stock_Item_Key(PK),WWI_Stock_Item_ID,Stock_Item,Color,Selling_Package,Buying_Package,Brand,Size,Lead_Time_Days,Quantity_Per_Outer,Is_Chiller_Stock,Barcode,Tax_Rate,Unit_Price,Recommended_Retail_Price,Typical_Weight_Per_Unit,Photo,Valid_From,Valid_To,Lineage_Key)
    - Dimension.Supplier(Supplier_Key(PK),WWI_Supplier_ID,Supplier,Category,Primary_Contact,Supplier_Reference,Payment_Days,Postal_Code,Valid_From,Valid_To,Lineage_Key)
"""

system_message="""
You are a smart AI assistant to help answer marketing analysis questions by querying data from Microsoft SQL Server Database and visualizing data with plotly. 
In the examples below, questions are broken down into one or several  parts to be analyzed and eventually to answer the main question.
The action after each thought can be a data query and data visualization code or it can be final answer. 
"""
few_shot_examples="""
<<Examples to follow:>>
Question: Show me top 20 best selling products in 2013
Thought 1: I need to query revenue for each month in 2013 for top 3 customers from Fact.Sales table and join with Dimension.Customer to get customer information and join with Dimension.Date to get time information. Then I need to group data by month and customer and sort data by revenue. Finally, I need to visualize data using line chart to show monthly revenue trends for each customer.
Action 1: Query[SELECT c.Customer, d.Calendar_Month_Label, SUM(s.Total_Including_Tax) AS Revenue FROM Fact.Sale s JOIN Dimension.Customer c ON s.Customer_Key = c.Customer_Key JOIN Dimension.Date d ON s.Invoice_Date_Key = d.Date WHERE d.Calendar_Year = 2013 GROUP BY c.Customer, d.Calendar_Month_Label HAVING c.Customer IN (SELECT TOP 3 c.Customer FROM Fact.Sale s JOIN Dimension.Customer c ON s.Customer_Key = c.Customer_Key JOIN Dimension.Date d ON s.Invoice_Date_Key = d.Date WHERE d.Calendar_Year = 2013 GROUP BY c.Customer ORDER BY SUM(s.Total_Including_Tax) DESC) ORDER BY c.Customer ASC, d.Calendar_Month_Number ASC;], Python[```\nimport plotly.express as px\n\ndef visualize_data(sql_result_df):\n    fig=px.line(sql_result_df, x='Calendar_Month_Label', y='Revenue', color='Customer', title='Monthly Revenue Trends in 2013 for Top 3 Customers')\n    return fig\n```]
Observation 1: ('42000', '[42000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Column "Dimension.Date.Calendar_Month_Number" is invalid in the ORDER BY clause because it is not contained in either an aggregate function or the GROUP BY clause. (4108) (SQLExecDirectW)')
Thought 2: SQL query returned error, I need to correct the syntax for my query based on the error message
Action 2: Query[SELECT c.Customer, d.Calendar_Month_Label, SUM(s.Total_Including_Tax) AS Revenue FROM Fact.Sale s JOIN Dimension.Customer c ON s.Customer_Key = c.Customer_Key JOIN Dimension.Date d ON s.Invoice_Date_Key = d.Date WHERE d.Calendar_Year = 2013 GROUP BY c.Customer, d.Calendar_Month_Label,d.Calendar_Month_Number HAVING c.Customer IN (SELECT TOP 3 c.Customer FROM Fact.Sale s JOIN Dimension.Customer c ON s.Customer_Key = c.Customer_Key JOIN Dimension.Date d ON s.Invoice_Date_Key = d.Date WHERE d.Calendar_Year = 2013 GROUP BY c.Customer ORDER BY SUM(s.Total_Including_Tax) DESC) ORDER BY c.Customer ASC, d.Calendar_Month_Number ASC;], Python[```\nimport plotly.express as px\n\ndef visualize_data(sql_result_df):\n    fig=px.line(sql_result_df, x='Calendar_Month_Label', y='Revenue', color='Customer', title='Monthly Revenue Trends in 2013 for Top 3 Customers')\n    return fig\n```]
Observation 2: Region                                      Stock_Item Total_Sales
0    Americas  "The Gu" red shirt XML tag t-shirt (Black) 3XL  1433516.40
1    Americas  "The Gu" red shirt XML tag t-shirt (Black) 3XS  1395759.60
Thought 3: The result answers the question
Action 3: Answer[The result is provided]
Question: Does 20% customer account for 80% of sales?
Thought 1: I need to determine the total sales generated by the company. 
Action 1: Query[SELECT SUM(Total_Including_Tax) AS Total_Sales FROM Fact.Sale]
Observation 1: 198043439.45
Thought 2: I now need to calculate the total sales for the top 20% of customers.
Action 2: Query[WITH CustomerSales AS ( SELECT c.Customer_Key, SUM(Total_Including_Tax) AS Total_Revenue FROM Fact.Sale s  JOIN Dimension.Customer c ON s.Customer_Key = c.Customer_Key  GROUP BY c.Customer_Key ), TopCustomers AS ( SELECT cs.Customer_Key FROM CustomerSales cs WHERE cs.Total_Revenue >= (SELECT TOP 1 PERCENTILE_CONT(0.2) WITHIN GROUP (ORDER BY Total_Revenue DESC) OVER () FROM CustomerSales) ) SELECT SUM(s.Total_Including_Tax) AS Top_Revenue FROM Fact.Sale s WHERE s.Customer_Key IN (SELECT Customer_Key FROM TopCustomers)]
Observation 2: 102904875.68
Thought 4: Now I need to divide the sales of top 20% customers by total sales
Action 4: Query[SELECT 102904875.68 / 198043439.45 AS Result ]
Observation 4: 0.51960759702913
Thought 5: Result came back and it is less than 80% so top 20% customers do not account for 80% of sales
Action 5: Answer[No, top 20% customers do not account for 80% of sales]
"""
openai.api_type = "azure"
openai.api_key = "d668777259a541a6beba2bdf43e1b519"  # SET YOUR OWN API KEY HERE
openai.api_base = "https://anildwaopenai2.openai.azure.com/" # SET YOUR RESOURCE ENDPOINT
openai.api_version = "2023-03-15-preview" 
max_response_tokens = 1250
token_limit= 4096
gpt_deployment="chatgpt"
database="WideWorldImportersDW"
dbserver="oaisqldemo.database.windows.net"
db_user="oaireaderuser"
db_password= "Oaiworkshop@password123"
analyzer = AnalyzeGPT(tables_structure, system_message,few_shot_examples, gpt_deployment,max_response_tokens,token_limit,database,dbserver,db_user, db_password)
st.title('Data Analysis Assistant')
question = st.text_area("Ask me a  question in sales")
if st.button("Submit"):  
    # Call the execute_query function with the user's question  
    
    analyzer.run(question, st)



