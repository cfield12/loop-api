# 🍽️ Loop - Discover Restaurants through Friends

**🌐 Live Application:** https://loopworld.me/

> **Currently in Beta** - Join the early community of food enthusiasts sharing their culinary discoveries!

## 🎯 What is Loop?

Loop revolutionizes how you discover and share restaurant experiences with your closest friends. Forget endless scrolling through generic restaurant apps – Loop creates your **personal culinary network** where trusted recommendations from people you actually know guide your dining adventures.

### 🌟 The Problem We Solve

Ever been overwhelmed by thousands of restaurant reviews from strangers? Loop eliminates the noise by creating a **private, curated dining experience** where only your friends' authentic reviews and discoveries populate your map. No fake reviews, no sponsored content – just real recommendations from people whose taste you trust.

### 🗺️ How It Works

**Your Personal Food Map:** Every restaurant where you or your friends have left reviews appears as interactive pins on an integrated Google Maps interface. Each pin tells a story – your friend's favorite hidden gem, that amazing brunch spot you discovered together, or the restaurant that became "your place."

**Smart Discovery:** 
- 🔍 **Intelligent Search:** Powered by Google Maps integration for precise location finding
- 📍 **Contextual Pins:** See exactly where your friends have dined and loved
- ⭐ **Authentic Reviews:** Read real experiences from people you trust
- 👥 **Friend Network:** Build your culinary circle by connecting with fellow food lovers

**Social Dining Made Simple:**
- **Friends Page:** Search, add, and accept connections with other food enthusiasts
- **Shared Experiences:** View combined restaurant collections from your entire friend network
- **Trust-Based Recommendations:** Only see reviews from people you've chosen to connect with

![image](https://github.com/user-attachments/assets/50e7bd5b-9f7c-4cfb-83c5-4678f9690925)

![image](https://github.com/user-attachments/assets/2d99ab43-2245-4d87-b665-2468669477f5)

## 🏗️ Technical Architecture

This repository contains the robust, scalable infrastructure that powers Loop's seamless user experience. Built with AWS best practices and designed for reliability, security, and performance.

### 🔌 API Services

**Loop API**
- Core application endpoints managing restaurant data, user interactions, and social features
- RESTful architecture with comprehensive error handling and data validation
- Optimized for real-time map interactions and review management

**Loop Auth API** 
- Secure authentication and user management system
- JWT-based session handling with refresh token rotation
- Integration with AWS Cognito for enterprise-grade security

### ☁️ AWS Infrastructure (CloudFormation Templates)

**🌐 Virtual Private Cloud (VPC)**
- **Elastic IPs:** Static IP addressing for consistent service availability
- **Multi-tier Architecture:** Public/private subnet separation for enhanced security
- **Internet Gateway:** Secure external connectivity
- **Route Tables:** Intelligent traffic routing and network segmentation
- **NAT Gateway:** Secure outbound connectivity for private resources

**🔐 Amazon Cognito**
- **User Pool:** Scalable user directory with custom attributes
- **App Client:** Secure client-side authentication configuration
- **Lambda Triggers:** Post-confirmation workflows for seamless user onboarding

**🗄️ Amazon RDS (MySQL)**
- **Private Database:** Secure, isolated data storage
- **High Availability:** Multi-AZ deployment for 99.99% uptime
- **Automated Backups:** Point-in-time recovery capabilities
- **Performance Optimization:** Read replicas for query optimization

**⚡ AWS Lambda Functions**
- **User Management:** Automated RDS user creation and profile setup
- **Media Processing:** Intelligent restaurant thumbnail uploads to S3
- **Data Lifecycle:** Secure user data deletion with GDPR compliance
- **Event-Driven Architecture:** Serverless functions triggered by user actions

### 🛡️ Security & Performance Features

- **Zero-Trust Architecture:** Private subnets and security groups
- **Encrypted Data Transit:** SSL/TLS encryption for all communications
- **Scalable Infrastructure:** Auto-scaling capabilities for traffic spikes
- **Cost Optimization:** Serverless components reduce operational overhead

## 🚀 Getting Started

Loop is currently in beta, offering early access to food enthusiasts who want to be part of the culinary discovery revolution. Join our growing community and start building your trusted restaurant network today.

## 👨‍💻 Development

This project represents a modern, cloud-native approach to social dining applications, showcasing:
- **Microservices Architecture:** Separated concerns for maintainability
- **Infrastructure as Code:** Reproducible, version-controlled deployments
- **Security-First Design:** Enterprise-grade authentication and data protection
- **Scalable Backend:** Designed to handle growing user bases and feature expansion

## 👤 Author & Acknowledgments

**Charlie Field** - Full-Stack Developer & Culinary Tech Enthusiast

*Building the future of social dining, one restaurant discovery at a time.*
