SELECT * FROM mydb.orders;
INSERT INTO mydb.orders (`Order ID`, `Customer ID`, `Product ID`, Quantity, Sales)
SELECT DISTINCT `Order ID`, `Customer ID`, `Product ID`, Quantity, Sales
FROM mydb.superstore_raw;
SELECT *
FROM mydb.orders
WHERE Sales > (SELECT AVG(Sales) FROM mydb.orders);
SELECT `Customer ID`, MAX(Sales) as MaxSales
FROM mydb.orders
GROUP BY `Customer ID`;
WITH TotalSalesPerCustomer AS (
    SELECT `Customer ID`, SUM(Sales) as TotalSales
    FROM mydb.orders
    GROUP BY `Customer ID`
)
SELECT * FROM TotalSalesPerCustomer;
WITH TotalSalesPerCustomer AS (
    SELECT `Customer ID`, SUM(Sales) as TotalSales
    FROM mydb.orders
    GROUP BY `Customer ID`
)
SELECT *
FROM TotalSalesPerCustomer 
WHERE TotalSales > (SELECT AVG(TotalSales) FROM TotalSalesPerCustomer);

WITH TotalSalesPerCustomer AS (
    SELECT `Customer ID`, SUM(Sales) as Total_Sales
    FROM mydb.orders
    GROUP BY `Customer ID`
)
SELECT `Customer ID`, Total_Sales,
       RANK() OVER (ORDER BY Total_Sales DESC) as SalesRank
FROM TotalSalesPerCustomer;
SELECT `Order ID`, `Customer ID`,
       ROW_NUMBER() OVER (PARTITION BY `Customer ID` ORDER BY `Order ID`) as RowNum
FROM mydb.orders;
WITH RankedCustomers AS (
    SELECT `Customer ID`, SUM(Sales) as TotalSales,
           RANK() OVER (ORDER BY SUM(Sales) DESC) as SalesRank
    FROM mydb.orders
    GROUP BY `Customer ID`
)
SELECT `Customer ID`, TotalSales
FROM RankedCustomers
WHERE SalesRank <= 3;
WITH TotalSalesPerCustomer AS (
    SELECT o.`Customer ID`, SUM(o.Sales) as TotalSales
    FROM mydb.orders o
    GROUP BY o.`Customer ID`
),
RankedCustomers AS (
    SELECT tspc.`Customer ID`, tspc.TotalSales,
           RANK() OVER (ORDER BY tspc.TotalSales DESC) as SalesRank
    FROM TotalSalesPerCustomer tspc
)
SELECT c.`Customer Name`, rc.TotalSales, rc.SalesRank
FROM RankedCustomers rc
JOIN mydb.customers c ON rc.`Customer ID` = c.`Customer ID`;


WITH RankedCustomers AS (
    SELECT c.`Customer Name`, SUM(o.Sales) as TotalSales,
           RANK() OVER (ORDER BY SUM(o.Sales) DESC) as SalesRank
    FROM mydb.orders o
    JOIN mydb.customers c ON o.`Customer ID` = c.`Customer ID`
    GROUP BY c.`Customer Name`
)
SELECT `Customer Name`, TotalSales, SalesRank
FROM RankedCustomers
WHERE SalesRank <= 5;

WITH RankedCustomers AS (
    SELECT c.`Customer Name`, SUM(o.Sales) as TotalSales,
           RANK() OVER (ORDER BY SUM(o.Sales) ) as SalesRank
    FROM mydb.orders o
    JOIN mydb.customers c ON o.`Customer ID` = c.`Customer ID`
    GROUP BY c.`Customer Name`
)
SELECT `Customer Name`, TotalSales,SalesRank
FROM RankedCustomers
WHERE SalesRank <= 5;

SELECT c.`Customer Name`
FROM mydb.customers c
JOIN (
    SELECT `Customer ID`, COUNT(DISTINCT `Order ID`) as OrderCount
    FROM mydb.orders
    GROUP BY `Customer ID`
    HAVING COUNT(DISTINCT `Order ID`) = 1
) oc ON c.`Customer ID` = oc.`Customer ID`;

WITH TotalSalesPerCustomer AS (
    SELECT o.`Customer ID`, SUM(o.Sales) as TotalSales
    FROM mydb.orders o
    GROUP BY o.`Customer ID`
)
SELECT c.`Customer Name`, tspc.TotalSales,c.`Customer ID`
FROM TotalSalesPerCustomer tspc
JOIN mydb.customers c ON tspc.`Customer ID` = c.`Customer ID`
WHERE tspc.TotalSales > (SELECT AVG(TotalSales) FROM TotalSalesPerCustomer);

SELECT c.`Customer Name`, o.`Order ID`, o.Sales
FROM mydb.orders o
JOIN mydb.customers c ON o.`Customer ID` = c.`Customer ID`
JOIN (
    SELECT `Customer ID`, MAX(Sales) as MaxSales
    FROM mydb.orders
    GROUP BY `Customer ID`
) m ON o.`Customer ID` = m.`Customer ID` AND o.Sales = m.MaxSales;


