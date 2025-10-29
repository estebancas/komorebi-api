# 🕯️ Komorebi API - E-commerce Development TODO

## 🎯 Phase 1: Essential E-commerce Features (Priority)

### Categories System

- [x] Create Category model with Firestore integration
- [x] Add category CRUD endpoints with Flask-RESTX
- [x] Update Product model to reference categories
- [x] Add category-based product filtering
- [x] Document category endpoints in Swagger

### Shopping Cart System

- [ ] Create Cart and CartItem models
- [ ] Add cart CRUD endpoints (add, remove, update quantities)
- [ ] Implement cart persistence for logged-in users
- [ ] Add guest cart with session management
- [ ] Implement cart totals calculation
- [ ] Add cart expiration/cleanup logic

### Basic Order Management

- [ ] Create Order and OrderItem models
- [ ] Add "create order from cart" endpoint
- [ ] Implement order status tracking
- [ ] Add order history endpoint for users
- [ ] Add order details endpoint

## 🚀 Phase 2: Core E-commerce Features

### User Address Management

- [ ] Create Address model
- [ ] Add address CRUD endpoints
- [ ] Support multiple addresses per user
- [ ] Add default address functionality
- [ ] Implement address validation

### Enhanced Inventory Management

- [ ] Add stock reservation during checkout
- [ ] Implement low stock alerts
- [ ] Add inventory history tracking
- [ ] Create inventory adjustment endpoints

### Payment Processing Foundation

- [ ] Create Payment model
- [ ] Add payment method management
- [ ] Prepare payment integration structure (Stripe/PayPal)
- [ ] Add payment status tracking

## 📈 Phase 3: Advanced Features

### Product Enhancements

- [ ] Add product reviews and ratings system
- [ ] Enhance product variants management
- [ ] Add related/recommended products
- [ ] Implement product availability status

### Admin & Management

- [ ] Create admin role system
- [ ] Add order management endpoints for admins
- [ ] Create inventory reports
- [ ] Add basic sales analytics

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

- [ ] Add API key authentication for admin endpoints
- [ ] Implement role-based access control
- [ ] Add input sanitization
- [ ] Optimize database queries
- [ ] Add caching layer (Redis)

### DevOps & Deployment

- [ ] Set up CI/CD pipeline
- [ ] Create Docker production setup
- [ ] Add environment-specific configs
- [ ] Set up monitoring and health checks
- [ ] Prepare database migration scripts

## 📝 Current API Status

### ✅ Completed

- User authentication (register/login)
- Product CRUD with pagination, search, and sorting
- User management
- Flask-RESTX documentation at `/docs/`
- JWT token authentication
- Basic error handling

### 🔄 In Progress

- None currently

## 💡 Notes & Ideas

- Consider implementing webhook support for payment processing
- Think about multi-currency support for international sales
- Plan for inventory management across multiple warehouses
- Consider implementing product bundles/packages
- Think about discount codes and promotions system
- Plan for customer support ticket system integration

## 🎯 Next Session Focus

**Recommended next task**: Start with Categories system as it's foundational for product organization and user experience.

---

_Last updated: 28/10/25_
_Remember to update this file as you complete tasks and add new requirements!_
