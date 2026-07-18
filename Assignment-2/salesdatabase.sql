SELECT * FROM mydb.sales;
SELECT *
FROM mydb.sales
WHERE Region = 'South';
SELECT *
FROM mydb.sales
WHERE Category = 'Furniture';
SELECT *
FROM mydb.sales
WHERE Sales > 2000;
SELECT *
FROM mydb.sales
WHERE `Order Date` > '2011-01-01';
SELECT SUM(Sales) AS Total_Sales
FROM mydb.sales;
SELECT MAX(Sales) AS Highest_Sale
FROM mydb.sales;
SELECT AVG(Sales) AS Average_Sales
FROM mydb.sales;
SELECT 
    Region, SUM(Sales) AS Total_Sales
FROM
    mydb.sales
GROUP BY Region;
SELECT Category,
AVG(Sales) AS Average_Sales
FROM mydb.sales
GROUP BY Category;
SELECT Region,
SUM(Quantity) AS Quantity_Sold
FROM mydb.sales
GROUP BY Region;
SELECT Category,
COUNT(*) AS Orders
FROM mydb.sales
GROUP BY Category;
SELECT `Customer Name`,
SUM(Quantity) AS Quantity
FROM mydb.sales
GROUP BY `Customer Name`
HAVING SUM(Quantity)>10;
SELECT `Customer Name`,
SUM(Sales) AS Total_Sales
FROM mydb.sales
GROUP BY `Customer Name`
ORDER BY Total_Sales DESC
LIMIT 10;
SELECT Region,
SUM(Profit) AS Profit
FROM mydb.sales
GROUP BY Region
ORDER BY Profit DESC;
SELECT `Product Name`,
SUM(Sales) AS Total_Sales
FROM mydb.sales
GROUP BY `Product Name`
ORDER BY Total_Sales DESC
LIMIT 10;
SELECT COUNT(*) FROM mydb.sales;
SELECT `Customer Name`, `Order Date`, COUNT(*) AS 
duplicate_count FROM mydb.sales GROUP BY `Customer Name`, `Order Date` 
HAVING COUNT(*) > 1;
