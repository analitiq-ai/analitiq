-- Create a comprehensive aggregate table for detailed reporting
CREATE TABLE detailed_event_user_sales_summary AS
SELECT
    e.eventid,
    e.eventname,
    e.starttime,
    v.venuename,
    v.venuecity,
    v.venuestate,
    v.venueseats,
    c.catgroup,
    c.catname,
    c.catdesc,
    d.caldate,
    d.day,
    d.week,
    d.month,
    d.qtr,
    d.year,
    d.holiday,
    l.listid,
    l.numtickets AS tickets_listed,
    l.priceperticket,
    l.totalprice AS listing_total_price,
    l.listtime,
    s.salesid,
    s.qtysold AS tickets_sold,
    s.pricepaid AS total_sales_price,
    s.commission AS sales_commission,
    s.sellerid,
    su.username AS seller_username,
    su.firstname AS seller_firstname,
    su.lastname AS seller_lastname,
    su.city AS seller_city,
    su.state AS seller_state,
    s.buyerid,
    bu.username AS buyer_username,
    bu.firstname AS buyer_firstname,
    bu.lastname AS buyer_lastname,
    bu.city AS buyer_city,
    bu.state AS buyer_state,
    s.saletime,
    SUM(s.qtysold) OVER (PARTITION BY e.eventid) AS total_tickets_sold_for_event,
    SUM(s.pricepaid) OVER (PARTITION BY e.eventid) AS total_revenue_for_event,
    AVG(s.pricepaid / s.qtysold) OVER (PARTITION BY e.eventid) AS avg_price_per_ticket_for_event,
    COUNT(s.salesid) OVER (PARTITION BY e.eventid) AS total_sales_transactions_for_event,
    SUM(s.qtysold) OVER (PARTITION BY su.userid) AS total_tickets_sold_by_seller,
    SUM(s.pricepaid) OVER (PARTITION BY su.userid) AS total_revenue_by_seller,
    AVG(s.commission) OVER (PARTITION BY su.userid) AS avg_commission_earned_by_seller,
    SUM(s.qtysold) OVER (PARTITION BY bu.userid) AS total_tickets_bought_by_buyer,
    SUM(s.pricepaid) OVER (PARTITION BY bu.userid) AS total_spent_by_buyer,
    COUNT(s.salesid) OVER (PARTITION BY bu.userid) AS total_purchases_by_buyer,
    AVG(s.pricepaid / s.qtysold) OVER (PARTITION BY bu.userid) AS avg_price_per_ticket_bought_by_buyer
FROM
    event e
        JOIN venue v ON e.venueid = v.venueid
        JOIN category c ON e.catid = c.catid
        JOIN date d ON e.dateid = d.dateid
        LEFT JOIN listing l ON e.eventid = l.eventid
        LEFT JOIN sales s ON l.listid = s.listid
        LEFT JOIN users su ON s.sellerid = su.userid
        LEFT JOIN users bu ON s.buyerid = bu.userid;

-- Additional columns for comprehensive analysis
ALTER TABLE detailed_event_user_sales_summary
    ADD COLUMN total_listings_for_event INTEGER,
ADD COLUMN total_listings_by_seller INTEGER,
ADD COLUMN total_purchases_by_buyer INTEGER;

-- Update the new columns with appropriate values
UPDATE detailed_event_user_sales_summary
SET
    total_listings_for_event = (
        SELECT COUNT(*)
        FROM listing l2
        WHERE l2.eventid = detailed_event_user_sales_summary.eventid
    ),
    total_listings_by_seller = (
        SELECT COUNT(*)
        FROM listing l2
        WHERE l2.sellerid = detailed_event_user_sales_summary.sellerid
    ),
    total_purchases_by_buyer = (
        SELECT COUNT(*)
        FROM sales s2
        WHERE s2.buyerid = detailed_event_user_sales_summary.buyerid
    );

-- Query to validate the aggregate table
SELECT * FROM detailed_event_user_sales_summary;
