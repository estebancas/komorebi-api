# 🕯️ Komorebi API - E-commerce Development TODO

## 🎯 Phase 1: Essential E-commerce Features (Priority)

### Categories System

- [x] Create Category model with Firestore integration
- [x] Add category CRUD endpoints with Flask-RESTX
- [x] Update Product model to reference categories
- [x] Add category-based product filtering
- [x] Document category endpoints in Swagger

### Shopping Cart System

- [x] Create Cart and CartItem models
- [x] Add cart CRUD endpoints (add, remove, update quantities)
- [x] Implement cart persistence for logged-in users
- [x] Add guest cart with session management
- [x] Implement cart totals calculation
- [x] Add cart expiration/cleanup logic

### Basic Order Management

- [x] Create Order and OrderItem models
- [x] Add "create order from cart" endpoint
- [x] Implement order status tracking
- [x] Add order history endpoint for users
- [x] Add order details endpoint

## 🚀 Phase 2: Core E-commerce Features

### User Address Management

- [x] Create Address model
- [x] Add address CRUD endpoints
- [x] Support multiple addresses per user
- [x] Add default address functionality
- [x] Implement address validation

### Enhanced Inventory Management

- [x] Add inventory history tracking (InventoryTransaction model with full audit trail)
- [x] Create inventory adjustment endpoints (adjust stock, restock, view history)
- [x] Implement low stock alerts (GET /inventory/low-stock endpoint)
- [x] Add admin inventory management endpoints with authentication
- [x] Integrate inventory logging with order processing
- [ ] Add stock reservation during checkout (hold stock for pending orders)
- [ ] Add image upload for payment proof (Firebase Storage)

### Payment Processing Foundation

- [x] Create Payment model
- [x] Add payment method management
- [x] Prepare payment integration structure (Stripe/PayPal)
- [x] Add payment status tracking
- [x] Add SINPE payment method to Order model
- [x] Add payment proof URL field for manual payment confirmation
- [x] Add admin payment confirmation fields and helper methods
- [x] Update Order API to accept payment_method and payment_proof_url during checkout
- [x] Create customer endpoint to upload payment proof (PUT /orders/{id}/payment-proof)
- [x] Create admin endpoint to confirm SINPE/manual payments (PUT /orders/{id}/confirm-payment)
- [x] Add admin endpoint to list orders awaiting payment confirmation (GET /orders/awaiting-confirmation)
- [ ] Add image upload functionality for proof of payment (Firebase Storage integration)

## 📈 Phase 3: Advanced Features

### Product Enhancements

- [ ] Add product reviews and ratings system
- [ ] Enhance product variants management
- [x] Add related/recommended products
- [ ] Implement product availability status

### Admin & Management

- [x] Create admin role system (User model has role management)
- [x] Add admin_required decorator for protected endpoints
- [x] Add admin payment confirmation endpoint
- [x] Add admin endpoint to list orders awaiting confirmation
- [x] Add order management endpoints for admins (update status, tracking numbers)
- [x] Add product management authentication (POST/PUT/DELETE require admin)
- [x] Create comprehensive inventory management system
- [ ] Create inventory reports and analytics
- [ ] Add basic sales analytics
- [ ] Add dashboard with key metrics

### Shipping & Tax

- [ ] Add shipping methods and rates
- [ ] Implement tax calculation
- [ ] Add shipping zones/regions

### Notifications

- [ ] Set up email service integration
- [ ] Add order confirmation emails
- [ ] Implement shipping notifications
- [ ] Add low stock alerts for admins

## 🔧 Technical Improvements

### Code Quality

- [ ] Add comprehensive unit tests
- [ ] Set up integration tests
- [ ] Add API rate limiting
- [ ] Implement proper logging
- [ ] Add request validation middleware

### Security & Performance

- [x] Implement role-based access control (admin_required decorator)
- [x] Secure product management endpoints (admin-only)
- [x] Secure inventory endpoints (admin-only)
- [ ] Add API key authentication for external integrations
- [ ] Add input sanitization
- [ ] Optimize database queries
- [ ] Add caching layer (Redis)
- [ ] Add rate limiting per user/IP

### DevOps & Deployment

- [ ] Set up CI/CD pipeline
- [x] Create Docker production setup
- [x] Add environment-specific configs
- [x] Set up monitoring and health checks
- [ ] Prepare database migration scripts

## 📝 Current API Status

### ✅ Completed

- User authentication (register/login)
- Product CRUD with pagination, search, and sorting
- Product management authentication (admin-only create/update/delete)
- Category management with CRUD endpoints
- User management
- Shopping cart system with CRUD operations
- Cart validation and stock checking
- Guest cart with session management
- Cart merge on login
- Order and OrderItem models with status tracking
- Order management API (create from cart, list, view, cancel)
- Stock reduction on order creation with inventory transaction logging
- User address management (CRUD, multiple addresses, default address, validation)
- Payment model (transaction tracking, status management, refunds)
- Payment method management (saved cards, CRUD API, default management)
- Payment gateway integration structure (Stripe-ready, PayPal-ready)
- SINPE payment support (Costa Rica) with manual confirmation workflow
- Admin role-based access control with admin_required decorator
- Admin endpoint to confirm manual payments (SINPE, bank transfer, cash on delivery)
- Admin endpoint to list orders awaiting payment confirmation
- **Inventory Management System:**
  - InventoryTransaction model for complete audit trail
  - Admin endpoints for stock adjustment and restocking
  - Automatic inventory logging on order placement
  - Low stock monitoring endpoint
  - Transaction history per product
  - Support for products with/without stock tracking
- Flask-RESTX documentation at `/docs/`
- JWT token authentication
- Basic error handling
- Debug logging for authentication troubleshooting

### 🔄 In Progress

- Adding authentication debug logging (completed - ready for removal once verified)
- Testing inventory management system in production

## 💡 Notes & Ideas

### Payment Integration Next Steps

- Implement actual Stripe API integration for charging saved payment methods
- Add Stripe webhook handlers for payment events (success, failure, refunds)
- Implement PayPal integration (future)
- Add payment retry logic for failed transactions
- Create admin payment dashboard

### General Ideas

- Consider implementing webhook support for payment processing
- Think about multi-currency support for international sales
- Consider implementing product bundles/packages
- Think about discount codes and promotions system
- Plan for customer support ticket system integration
- Setup proper unit-testing
- Consider stock reservation system for pending orders
- Add inventory forecasting based on sales trends
- Implement automated low-stock notifications (email/SMS)
- Add bulk inventory import/export via CSV

---

_Last updated: 01/11/25_
_Remember to update this file as you complete tasks and add new requirements!_
