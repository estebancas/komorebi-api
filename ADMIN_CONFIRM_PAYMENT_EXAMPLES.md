# Admin Payment Confirmation - API Examples

Complete guide for admins to confirm SINPE and manual payments.

---

## Prerequisites

### 1. Create Admin User with Role

First, you need an admin user with the 'admin' role:

```bash
# 1. Register admin user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@komorebi.com",
    "password": "admin123",
    "first_name": "Admin",
    "last_name": "Komorebi"
  }'

# 2. Create 'admin' role (if not exists)
# You'll need to do this programmatically or via direct database access
# Example Python script:
```

```python
from app.models.role import Role
from app.models.user import User
from app.services.firebase_service import initialize_firebase

initialize_firebase()

# Create admin role
admin_role = Role(name='admin', description='Administrator')
admin_role_id = admin_role.save()

# Assign admin role to user
admin_user = User.get_by_email('admin@komorebi.com')
admin_user.add_role(admin_role_id)
admin_user.save()

print(f"Admin role created: {admin_role_id}")
print(f"Admin user updated: {admin_user.email}")
```

### 2. Login as Admin

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@komorebi.com",
    "password": "admin123"
  }'

# Save the token
# ADMIN_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## Admin Workflow

### Step 1: View Orders Awaiting Confirmation

#### Option A: Use the Dedicated Admin Endpoint (Recommended)

This endpoint automatically filters orders that need confirmation:

```bash
curl -X GET "http://localhost:5000/api/orders/awaiting-confirmation" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "orders": [
    {
      "id": "order_sinpe123",
      "order_number": "ORD-20251030-XYZ789",
      "status": "pending",
      "payment_method": "sinpe",
      "payment_proof_url": "https://storage.../sinpe_proof_001.jpg",
      "payment_confirmed": false,
      "payment_confirmed_at": null,
      "payment_confirmed_by": null,
      "total": 44000,
      "shipping_address": {
        "email": "customer@example.com"
      },
      "created_at": "2025-10-30T04:00:00Z"
    },
    {
      "id": "order_bank456",
      "order_number": "ORD-20251030-ABC456",
      "status": "pending",
      "payment_method": "bank_transfer",
      "payment_proof_url": "https://storage.../bank_proof_002.jpg",
      "payment_confirmed": false,
      "payment_confirmed_at": null,
      "payment_confirmed_by": null,
      "total": 15500,
      "shipping_address": {
        "email": "juan@example.com"
      },
      "created_at": "2025-10-30T03:30:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "per_page": 2
}
```

**What this endpoint does automatically:**
- ✅ Filters only orders with manual payment methods (SINPE, bank transfer, cash on delivery)
- ✅ Shows only orders with `payment_confirmed = false`
- ✅ Shows only orders with `status = 'pending'`
- ✅ Shows only orders with `payment_proof_url` uploaded
- ✅ Sorts by creation date (oldest first) so you see the most urgent orders
- ✅ Requires admin authentication

#### Option B: Get All Pending Orders and Filter Manually

If you need more flexibility, get all pending orders:

```bash
curl -X GET "http://localhost:5000/api/orders?status=pending" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

Then filter in your admin dashboard by checking:
- `payment_method` in `['sinpe', 'bank_transfer', 'cash_on_delivery']`
- `payment_confirmed === false`
- `payment_proof_url !== null`

---

### Step 2: View Payment Proof Image

Get order details to view the proof URL:

```bash
curl -X GET http://localhost:5000/api/orders/order_sinpe123 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response includes:**
```json
{
  "payment_proof_url": "https://firebasestorage.googleapis.com/v0/b/komorebi/receipts/sinpe_proof_001.jpg"
}
```

Admin can open this URL in browser to view the screenshot.

---

### Step 3: Confirm Payment

After verifying the SINPE transfer in your bank account:

```bash
curl -X PUT http://localhost:5000/api/orders/order_sinpe123/confirm-payment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "admin_notes": "Verified SINPE transfer of ₡44,000 to phone 8888-8888. Reference: SINPE-20251030-001"
  }'
```

**Response (200 OK):**
```json
{
  "id": "order_sinpe123",
  "order_number": "ORD-20251030-XYZ789",
  "status": "processing",
  "payment_method": "sinpe",
  "payment_status": "paid",
  "payment_confirmed": true,
  "payment_confirmed_at": "2025-10-30T05:15:00.000000+00:00",
  "payment_confirmed_by": "admin_abc123",
  "payment_proof_url": "https://storage.../sinpe_proof_001.jpg",
  "admin_notes": "Payment confirmed: Verified SINPE transfer of ₡44,000 to phone 8888-8888. Reference: SINPE-20251030-001",
  "paid_at": "2025-10-30T05:15:00.000000+00:00",
  "total": 44000
}
```

**What happens automatically:**
- ✅ `payment_confirmed` set to `true`
- ✅ `payment_confirmed_at` set to current timestamp
- ✅ `payment_confirmed_by` set to admin user ID
- ✅ `payment_status` set to `'paid'`
- ✅ `paid_at` set to current timestamp
- ✅ Order `status` changes from `'pending'` to `'processing'`
- ✅ Admin notes appended with confirmation message

---

## Error Scenarios

### 1. Non-Admin User Tries to Confirm

```bash
# Regular user token (not admin)
curl -X PUT http://localhost:5000/api/orders/order_sinpe123/confirm-payment \
  -H "Authorization: Bearer USER_TOKEN"
```

**Response (403 Forbidden):**
```json
{
  "error": "Admin access required"
}
```

### 2. No Payment Proof Uploaded

```bash
curl -X PUT http://localhost:5000/api/orders/order_xyz/confirm-payment \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response (400 Bad Request):**
```json
{
  "message": "Cannot confirm payment without proof. Customer must upload payment proof first."
}
```

### 3. Wrong Payment Method

```bash
# Order with credit card payment
curl -X PUT http://localhost:5000/api/orders/order_creditcard/confirm-payment \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response (400 Bad Request):**
```json
{
  "message": "This endpoint is only for manual payment methods (SINPE, bank transfer, cash on delivery). This order uses: credit_card"
}
```

### 4. Already Confirmed

```bash
curl -X PUT http://localhost:5000/api/orders/order_sinpe123/confirm-payment \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response (400 Bad Request):**
```json
{
  "message": "Payment has already been confirmed"
}
```

---

## Complete Admin Dashboard Flow

### Get Pending SINPE Payments

Create a helper endpoint or filter in your frontend:

```python
# Example: Get all orders awaiting confirmation
from app.models.order import Order

def get_orders_awaiting_confirmation():
    all_pending = Order.get_all(status=Order.STATUS_PENDING)

    awaiting_confirmation = [
        order for order in all_pending
        if order.is_awaiting_payment_confirmation()
    ]

    return awaiting_confirmation
```

### Admin Dashboard UI Flow

```
┌─────────────────────────────────────────────────────────┐
│  SINPE Payments Awaiting Confirmation (3)               │
├─────────────────────────────────────────────────────────┤
│  Order: ORD-20251030-XYZ789                             │
│  Customer: customer@example.com                         │
│  Amount: ₡44,000                                        │
│  Date: 2025-10-30 04:00                                 │
│  Proof: [View Image] 📷                                 │
│  Actions: [✓ Confirm] [✗ Reject]                        │
├─────────────────────────────────────────────────────────┤
│  Order: ORD-20251030-ABC123                             │
│  Customer: juan@example.com                             │
│  Amount: ₡15,500                                        │
│  Date: 2025-10-30 03:30                                 │
│  Proof: [View Image] 📷                                 │
│  Actions: [✓ Confirm] [✗ Reject]                        │
└─────────────────────────────────────────────────────────┘

When admin clicks "✓ Confirm":
1. Show modal: "Enter confirmation notes (optional)"
2. Call: PUT /api/orders/{id}/confirm-payment
3. Show success message
4. Order moves to "Processing Orders" section
5. Customer receives email notification (future)
```

---

## Testing the Complete Flow

### Quick Test Script

```bash
#!/bin/bash

BASE_URL="http://localhost:5000/api"

echo "=== Testing Admin Payment Confirmation ==="

# 1. Create admin token (assuming admin user exists)
echo "1. Logging in as admin..."
ADMIN_LOGIN=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@komorebi.com",
    "password": "admin123"
  }')

ADMIN_TOKEN=$(echo $ADMIN_LOGIN | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Admin token: ${ADMIN_TOKEN:0:20}..."

# 2. Get orders awaiting confirmation (using new dedicated endpoint)
echo ""
echo "2. Getting orders awaiting confirmation..."
AWAITING_ORDERS=$(curl -s -X GET "$BASE_URL/orders/awaiting-confirmation" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

echo "Orders awaiting confirmation:"
echo "$AWAITING_ORDERS" | head -20

# Extract first order ID (you'll need jq for this)
# ORDER_ID=$(echo $AWAITING_ORDERS | jq -r '.orders[0].id')

# For testing, use a known order ID
ORDER_ID="order_sinpe123"

# 3. View order details
echo ""
echo "3. Viewing order details..."
curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | head -20

# 4. Confirm payment
echo ""
echo "4. Confirming payment..."
CONFIRM_RESPONSE=$(curl -s -X PUT "$BASE_URL/orders/$ORDER_ID/confirm-payment" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "admin_notes": "Verified SINPE transfer of ₡44,000. Ref: SINPE-001"
  }')

echo "Payment confirmed!"
echo "Order status: $(echo $CONFIRM_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)"
echo "Payment status: $(echo $CONFIRM_RESPONSE | grep -o '"payment_status":"[^"]*' | cut -d'"' -f4)"
echo "Payment confirmed: $(echo $CONFIRM_RESPONSE | grep -o '"payment_confirmed":[^,}]*' | cut -d':' -f2)"
```

---

## API Summary

### Admin Endpoints

#### 1. Get Orders Awaiting Confirmation
```
GET /api/orders/awaiting-confirmation
```

**Authentication:**
- Requires JWT token
- Requires 'admin' role

**Response (200 OK):**
Returns list of orders that need manual payment confirmation:
- Automatically filtered to manual payment methods only
- Only shows unconfirmed orders with proof uploaded
- Sorted by creation date (oldest first)

**Error Responses:**
- **401 Unauthorized**: No token or invalid token
- **403 Forbidden**: User is not admin

---

#### 2. Confirm Payment
```
PUT /api/orders/{order_id}/confirm-payment
```

**Authentication:**
- Requires JWT token
- Requires 'admin' role

**Request Body:**
```json
{
  "admin_notes": "Optional notes about the confirmation"
}
```

**Response (200 OK):**
Returns full order object with updated fields:
- `payment_confirmed`: true
- `payment_confirmed_at`: timestamp
- `payment_confirmed_by`: admin user ID
- `status`: "processing"
- `payment_status`: "paid"
- `paid_at`: timestamp

**Error Responses:**
- **401 Unauthorized**: No token or invalid token
- **403 Forbidden**: User is not admin
- **404 Not Found**: Order doesn't exist
- **400 Bad Request**:
  - Not a manual payment method
  - Payment already confirmed
  - No payment proof uploaded

---

## Integration Checklist

- [ ] Create admin role in database
- [ ] Assign admin role to admin users
- [x] Create API endpoint to list orders awaiting confirmation (GET /api/orders/awaiting-confirmation)
- [ ] Create admin dashboard UI that calls the awaiting-confirmation endpoint
- [ ] Add "View Proof" button to open image in new tab
- [ ] Add "Confirm Payment" button with notes input
- [ ] Show success/error messages
- [ ] Refresh order list after confirmation
- [ ] (Optional) Send email notification to customer
- [ ] (Optional) Log admin actions for audit trail

---

## Security Notes

1. **Only admins can confirm**: The `@admin_required` decorator ensures only users with 'admin' role can access this endpoint

2. **Audit trail**: The system records:
   - Who confirmed the payment (`payment_confirmed_by`)
   - When it was confirmed (`payment_confirmed_at`)
   - Admin notes about the confirmation

3. **Cannot be reversed**: Once confirmed, payment cannot be unconfirmed. Admin would need to refund the order instead.

4. **Proof required**: System prevents confirmation without uploaded proof to ensure accountability.
