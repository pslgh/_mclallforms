# Main
1. In main page, after clicking Logout button, do not immediately close the application, but just go back to the log in page instead.

# Expense
1. The default currencies should be [THB, USD, VND, PHP, MYR, KYAT, SGD, KRW, YEN, CNY, LKP]
When third currency is selected, the two exchange rate inputs are required which are THB/USD and ThirdCurrency/USD. These will be used in the conversion of expense amount to THB. Because in final report, all expenses will be converted to THB. Please modify layout inside the Fund Currency Information box to optimize the display area of input fields.
2. The receipt type selection shall be selected one type only (official or non-official).
3. In history tab, after clicking view button, the expense form should be opened in a new window with all the details that cannot be edited with print button available. After clicking edit button, the expense form should be opened in a the first tab with all the details that can be edited.
4. Add new more tab called 'config'. In this tab, for user to be able to add or edit list of expense categories and currencies.
5. The saved form ID should be unique and auto-generated with format 'EXP-Username-YYYY-MM-DD-hhmmss'

6. When the Work Location is Abroad, the work country selection should be available. Bring all countries in the global to the selection list. 
7. The third currency selection input number should be float number. Now, I cannot input more than 99.000. Please fix.

Further improvement
8. Modify the expense layout by arrange the Project Information box and Fund Currency Information box side by side. This will gain more space for expense table.
9. Modify the expense table, when the Add Expense button is clicked, do not use pop-up window to add expense item. Instead, just add new row to the expense table. Embed the expense category selection and receipt type selection into the expense table. And combine the receipt type selection into the single column. In action column, add duplicate button.

10. The remaining amount conversion calculation from the third currency to THB is wrong. Please fix. The correct calculation is to convert the third currency amount to USD first, and then convert the USD amount to THB using the THB to USD rate.
11. Modify layout at bottom by arranging the expense summary and issued by section side by side.

12. In history tab, the history table should not be editable. Please fix.
13. In history tab, after clicking view button, the expense form is opened in a new window to show the expense report, ready to be export to PDF. Please modify the layout to be look similar to the input form and suitable for A4 paper size with Export to PDF button instead of Print button.

14. The previewed report cannot be resized in vertical direction (when clicked the edge was moved away), please fixed. It should be resizable in both directions. However, the exported PDF shall be fitted in A4 paper width (multipage A4 is acceptable). Additionally, if the column width is less than the content width, the content text should be wrappedable in the previewed report and exported PDF.

15. Your layout in your PDF is still incorrect. Please place the Project Information and Fund Currency Information in side by side and place in the same box. Then the table of expense items below the box. After that, place the Summary and Issue By side-by-side in the same box. Then place the signature area below the box. 
