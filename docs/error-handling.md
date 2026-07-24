# Error Handling

## Objective

Error handling ensures that invalid requests are managed correctly and meaningful responses are returned to the client.

---

## Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request Successful |
| 201 | Resource Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Resource Not Found |
| 409 | Conflict |
| 500 | Internal Server Error |

---

## Validation Errors

Examples include:

- Missing required fields
- Invalid appointment date
- Invalid doctor ID
- Duplicate appointment booking

---

## Exception Handling

The application should return descriptive error messages while preventing system crashes.