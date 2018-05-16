SELECT id FROM Payments
	WHERE bank_account = ?
	AND sort_code = ?
	AND payee_name = ?
	AND building_society_num = ?