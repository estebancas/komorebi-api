# SINPE Payment Flow - API Examples

Complete API call examples for testing SINPE payment workflow in Komorebi API.

---

## Prerequisites

1. **Start the server:**
   ```bash
   python app.py
   ```

2. **Get authentication token:**
   ```bash
   # Register a user
   curl -X POST http://localhost:5000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "customer@example.com",
       "password": "password123",
       "first_name": "Juan",
       "last_name": "Pérez"
     }'

   # Login to get token
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "customer@example.com",
       "password": "password123"
     }'

   # Save the token from response
   # TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
   ```

---

## Step 1: Create a Category

```bash
curl -X POST http://localhost:5000/api/categories/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Velas Aromáticas",
    "description": "Velas artesanales con aromas naturales",
    "slug": "velas-aromaticas"
  }'
```

**Response:**
```json
{
  "id": "cat_abc123",
  "name": "Velas Aromáticas",
  "description": "Velas artesanales con aromas naturales",
  "slug": "velas-aromaticas",
  "is_active": true
}
```

**Save the category ID:** `cat_abc123`

---

## Step 2: Create 2 Products

### Product 1: Vela de Lavanda

```bash
curl -X POST http://localhost:5000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Vela de Lavanda",
    "description": "Vela aromática de lavanda relajante, 100% natural",
    "price": 8500,
    "category_id": "cat_abc123",
    "stock": 50,
    "track_quantity": true,
    "requires_selling_stock": false,
    "media": [
      {
        "url": "https://example.com/lavanda.jpg",
        "alt_text": "Vela de Lavanda"
      }
    ],
    "weight": 250,
    "size": "8oz"
  }'
```

**Response:**
```json
{
  "id": "prod_lavanda123",
  "name": "Vela de Lavanda",
  "price": 8500,
  "stock": 50,
  ...
}
```

**Save product ID:** `prod_lavanda123`

### Product 2: Vela de Vainilla

```bash
curl -X POST http://localhost:5000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Vela de Vainilla",
    "description": "Vela aromática de vainilla dulce y reconfortante",
    "price": 9000,
    "category_id": "cat_abc123",
    "stock": 30,
    "track_quantity": true,
    "requires_selling_stock": false,
    "media": [
      {
        "url": "https://example.com/vainilla.jpg",
        "alt_text": "Vela de Vainilla"
      }
    ],
    "weight": 250,
    "size": "8oz"
  }'
```

**Response:**
```json
{
  "id": "prod_vainilla456",
  "name": "Vela de Vainilla",
  "price": 9000,
  "stock": 30,
  ...
}
```

**Save product ID:** `prod_vainilla456`

---

## Step 3: Add Products to Cart

### Add Vela de Lavanda (Quantity: 2)

```bash
curl -X POST http://localhost:5000/api/carts/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "product_id": "prod_lavanda123",
    "quantity": 2
  }'
```

**Response:**
```json
{
  "id": "cart_xyz789",
  "user_id": "user_abc123",
  "items": [
    {
      "product_id": "prod_lavanda123",
      "product_name": "Vela de Lavanda",
      "quantity": 2,
      "unit_price": 8500,
      "total_price": 17000
    }
  ],
  "subtotal": 17000,
  "total": 17000,
  "item_count": 1,
  "total_items": 2
}
```

### Add Vela de Vainilla (Quantity: 3)

```bash
curl -X POST http://localhost:5000/api/carts/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "product_id": "prod_vainilla456",
    "quantity": 3
  }'
```

**Response:**
```json
{
  "id": "cart_xyz789",
  "user_id": "user_abc123",
  "items": [
    {
      "product_id": "prod_lavanda123",
      "product_name": "Vela de Lavanda",
      "quantity": 2,
      "unit_price": 8500,
      "total_price": 17000
    },
    {
      "product_id": "prod_vainilla456",
      "product_name": "Vela de Vainilla",
      "quantity": 3,
      "unit_price": 9000,
      "total_price": 27000
    }
  ],
  "subtotal": 44000,
  "total": 44000,
  "item_count": 2,
  "total_items": 5
}
```

### View Cart

```bash
curl -X GET http://localhost:5000/api/carts/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Step 4: Create Order with SINPE Payment Method

```bash
curl -X POST http://localhost:5000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "payment_method": "sinpe",
    "shipping_address": {
      "street": "Avenida Central, Casa 456",
      "city": "San José",
      "state": "San José",
      "postal_code": "10101",
      "country": "Costa Rica",
      "phone": "8888-7777"
    },
    "billing_address": {
      "street": "Avenida Central, Casa 456",
      "city": "San José",
      "state": "San José",
      "postal_code": "10101",
      "country": "Costa Rica",
      "phone": "8888-7777"
    },
    "customer_notes": "Por favor entregar en la mañana"
  }'
```

**Response:**
```json
{
  "id": "order_sinpe123",
  "order_number": "ORD-20251030-XYZ789",
  "user_id": "user_abc123",
  "status": "pending",
  "payment_method": "sinpe",
  "payment_status": null,
  "payment_confirmed": false,
  "payment_proof_url": null,
  "items": [
    {
      "product_id": "prod_lavanda123",
      "product_name": "Vela de Lavanda",
      "quantity": 2,
      "unit_price": 8500,
      "total_price": 17000
    },
    {
      "product_id": "prod_vainilla456",
      "product_name": "Vela de Vainilla",
      "quantity": 3,
      "unit_price": 9000,
      "total_price": 27000
    }
  ],
  "subtotal": 44000,
  "total": 44000,
  "shipping_address": {
    "street": "Avenida Central, Casa 456",
    "city": "San José",
    "state": "San José",
    "postal_code": "10101",
    "country": "Costa Rica",
    "phone": "8888-7777"
  },
  "customer_notes": "Por favor entregar en la mañana",
  "created_at": "2025-10-30T04:00:00.000000+00:00"
}
```

**Save order ID:** `order_sinpe123`
**Save order number:** `ORD-20251030-XYZ789`

---

## Step 5: Upload Proof of Payment (Screenshot)

**After customer makes SINPE transfer and takes screenshot:**

```bash
curl -X PUT http://localhost:5000/api/orders/order_sinpe123/payment-proof \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "payment_proof_url": "https://firebasestorage.googleapis.com/v0/b/komorebi/receipts/sinpe_proof_20251030_001.jpg"
  }'
```

**Response:**
```json
{
  "id": "order_sinpe123",
  "order_number": "ORD-20251030-XYZ789",
  "status": "pending",
  "payment_method": "sinpe",
  "payment_proof_url": "https://firebasestorage.googleapis.com/v0/b/komorebi/receipts/sinpe_proof_20251030_001.jpg",
  "payment_confirmed": false,
  "payment_confirmed_at": null,
  "payment_confirmed_by": null,
  "total": 44000,
  ...
}
```

---

## Step 6: View Order Details

```bash
curl -X GET http://localhost:5000/api/orders/order_sinpe123 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Complete Flow - Single Script

Here's a complete bash script to test the entire flow:

```bash
#!/bin/bash

BASE_URL="http://localhost:5000/api"

echo "=== SINPE Payment Flow Test ==="
echo ""

# 1. Register and Login
echo "1. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "password123",
    "first_name": "Juan",
    "last_name": "Pérez"
  }')
echo "Registered: $REGISTER_RESPONSE"

echo ""
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "password123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Token obtained: ${TOKEN:0:20}..."

# 2. Create Category
echo ""
echo "3. Creating category..."
CATEGORY_RESPONSE=$(curl -s -X POST $BASE_URL/categories/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Velas Aromáticas",
    "description": "Velas artesanales con aromas naturales",
    "slug": "velas-aromaticas"
  }')

CATEGORY_ID=$(echo $CATEGORY_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Category created: $CATEGORY_ID"

# 3. Create Products
echo ""
echo "4. Creating products..."
PRODUCT1_RESPONSE=$(curl -s -X POST $BASE_URL/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"name\": \"Vela de Lavanda\",
    \"description\": \"Vela aromática de lavanda relajante\",
    \"price\": 8500,
    \"category_id\": \"$CATEGORY_ID\",
    \"stock\": 50,
    \"track_quantity\": true
  }")

PRODUCT1_ID=$(echo $PRODUCT1_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Product 1 created: $PRODUCT1_ID - Vela de Lavanda (₡8,500)"

PRODUCT2_RESPONSE=$(curl -s -X POST $BASE_URL/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"name\": \"Vela de Vainilla\",
    \"description\": \"Vela aromática de vainilla dulce\",
    \"price\": 9000,
    \"category_id\": \"$CATEGORY_ID\",
    \"stock\": 30,
    \"track_quantity\": true
  }")

PRODUCT2_ID=$(echo $PRODUCT2_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Product 2 created: $PRODUCT2_ID - Vela de Vainilla (₡9,000)"

# 4. Add to Cart
echo ""
echo "5. Adding products to cart..."
curl -s -X POST $BASE_URL/carts/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"product_id\": \"$PRODUCT1_ID\",
    \"quantity\": 2
  }" > /dev/null

echo "Added 2x Vela de Lavanda"

curl -s -X POST $BASE_URL/carts/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"product_id\": \"$PRODUCT2_ID\",
    \"quantity\": 3
  }" > /dev/null

echo "Added 3x Vela de Vainilla"

# 5. View Cart
echo ""
echo "6. Viewing cart..."
CART_RESPONSE=$(curl -s -X GET $BASE_URL/carts/ \
  -H "Authorization: Bearer $TOKEN")

CART_TOTAL=$(echo $CART_RESPONSE | grep -o '"total":[0-9.]*' | head -1 | cut -d':' -f2)
echo "Cart Total: ₡$CART_TOTAL"

# 6. Create Order with SINPE
echo ""
echo "7. Creating order with SINPE payment method..."
ORDER_RESPONSE=$(curl -s -X POST $BASE_URL/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "payment_method": "sinpe",
    "shipping_address": {
      "street": "Avenida Central, Casa 456",
      "city": "San José",
      "state": "San José",
      "postal_code": "10101",
      "country": "Costa Rica",
      "phone": "8888-7777"
    },
    "customer_notes": "Por favor entregar en la mañana"
  }')

ORDER_ID=$(echo $ORDER_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
ORDER_NUMBER=$(echo $ORDER_RESPONSE | grep -o '"order_number":"[^"]*' | cut -d'"' -f4)

echo "Order created successfully!"
echo "Order ID: $ORDER_ID"
echo "Order Number: $ORDER_NUMBER"
echo "Payment Method: SINPE"
echo "Total: ₡$CART_TOTAL"

# 7. Upload Payment Proof
echo ""
echo "8. Uploading payment proof..."
PROOF_RESPONSE=$(curl -s -X PUT $BASE_URL/orders/$ORDER_ID/payment-proof \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "payment_proof_url": "https://storage.googleapis.com/komorebi/receipts/sinpe_proof_001.jpg"
  }')

echo "Payment proof uploaded!"
echo ""
echo "=== Order awaiting admin confirmation ==="
echo "Order Number: $ORDER_NUMBER"
echo "Order ID: $ORDER_ID"
echo ""
echo "Next steps:"
echo "- Admin views pending payments"
echo "- Admin confirms SINPE transfer"
echo "- Order status changes to 'processing'"
```

Save this as `test_sinpe_flow.sh` and run:
```bash
chmod +x test_sinpe_flow.sh
./test_sinpe_flow.sh
```

---

## Alternative: Using Postman

Import this collection:

```json
{
  "info": {
    "name": "Komorebi - SINPE Payment Flow",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Register User",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": "{{base_url}}/auth/register",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"customer@example.com\",\n  \"password\": \"password123\",\n  \"first_name\": \"Juan\",\n  \"last_name\": \"Pérez\"\n}"
        }
      }
    },
    {
      "name": "2. Login",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": "{{base_url}}/auth/login",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"customer@example.com\",\n  \"password\": \"password123\"\n}"
        }
      }
    },
    {
      "name": "3. Create Category",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/categories/",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"name\": \"Velas Aromáticas\",\n  \"description\": \"Velas artesanales\",\n  \"slug\": \"velas-aromaticas\"\n}"
        }
      }
    },
    {
      "name": "4. Create Product 1 - Lavanda",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/products/",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"name\": \"Vela de Lavanda\",\n  \"description\": \"Vela aromática de lavanda\",\n  \"price\": 8500,\n  \"category_id\": \"{{category_id}}\",\n  \"stock\": 50,\n  \"track_quantity\": true\n}"
        }
      }
    },
    {
      "name": "5. Create Product 2 - Vainilla",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/products/",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"name\": \"Vela de Vainilla\",\n  \"description\": \"Vela aromática de vainilla\",\n  \"price\": 9000,\n  \"category_id\": \"{{category_id}}\",\n  \"stock\": 30,\n  \"track_quantity\": true\n}"
        }
      }
    },
    {
      "name": "6. Add Product 1 to Cart",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/carts/items",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"product_id\": \"{{product1_id}}\",\n  \"quantity\": 2\n}"
        }
      }
    },
    {
      "name": "7. Add Product 2 to Cart",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/carts/items",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"product_id\": \"{{product2_id}}\",\n  \"quantity\": 3\n}"
        }
      }
    },
    {
      "name": "8. View Cart",
      "request": {
        "method": "GET",
        "header": [{"key": "Authorization", "value": "Bearer {{token}}"}],
        "url": "{{base_url}}/carts/"
      }
    },
    {
      "name": "9. Create Order with SINPE",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/orders/",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"payment_method\": \"sinpe\",\n  \"shipping_address\": {\n    \"street\": \"Avenida Central, Casa 456\",\n    \"city\": \"San José\",\n    \"state\": \"San José\",\n    \"postal_code\": \"10101\",\n    \"country\": \"Costa Rica\",\n    \"phone\": \"8888-7777\"\n  },\n  \"customer_notes\": \"Por favor entregar en la mañana\"\n}"
        }
      }
    },
    {
      "name": "10. Upload Payment Proof",
      "request": {
        "method": "PUT",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{token}}"}
        ],
        "url": "{{base_url}}/orders/{{order_id}}/payment-proof",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"payment_proof_url\": \"https://storage.googleapis.com/komorebi/receipts/sinpe_proof_001.jpg\"\n}"
        }
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:5000/api"}
  ]
}
```

---

## Expected Results

✅ **Cart Total:** ₡44,000
- 2x Vela de Lavanda @ ₡8,500 = ₡17,000
- 3x Vela de Vainilla @ ₡9,000 = ₡27,000

✅ **Order Status:** `pending`
✅ **Payment Method:** `sinpe`
✅ **Payment Confirmed:** `false`
✅ **Payment Proof URL:** Set after upload
✅ **Awaiting Confirmation:** `true`

---

## Next Steps

After order creation, the frontend should:
1. Display SINPE phone number (from config)
2. Show order total in colones
3. Provide upload button for payment proof
4. Show "awaiting confirmation" status

Admin should see the order in pending payments dashboard with the uploaded proof image.
