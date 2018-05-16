IF NOT EXISTS
	(SELECT * FROM Payments
		WHERE bank_account = ?
		AND sort_code = ?
		AND payee_name = ?
		AND building_society_num = ?)
	INSERT INTO Payments (
		bank_account,
		sort_code,
		payee_name,
		building_society_num)
	VALUES (
		?,
		?,
		?,
		?)