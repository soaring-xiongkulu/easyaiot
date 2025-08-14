# EasyAIoT Gateway

[中文文档](README.md) | English

## Project Introduction

EasyAIoT Gateway is an API gateway service based on Spring Cloud Gateway, providing unified API access entry for the entire system. It implements functions such as routing forwarding, load balancing, security authentication, cross-domain support, and grayscale publishing.

## System Architecture

The gateway service is a core component of the EasyAIoT IoT platform, mainly responsible for:
- API routing and forwarding
- Authentication and authorization verification
- Cross-domain support processing
- Load balancing
- Grayscale publishing support
- Service integration and protocol adaptation

## Technical Stack

- Core framework: Spring Boot 2.7.0 + Spring Cloud 2021.0.5
- Gateway component: Spring Cloud Gateway
- Service registration and discovery: Nacos
- Configuration management: Nacos Config
- Load balancing: Spring Cloud LoadBalancer
- Security authentication: OAuth2 + JWT

## Main Functions

### 1. Routing Management
Supports dynamic routing configuration based on Nacos configuration center, which can be adjusted without restarting the service.

### 2. Security Authentication
- Token-based authentication verification
- Support for multi-tenant access control
- User identity information parsing and forwarding

### 3. Cross-domain Support
- Full cross-domain request support
- Handling of preflight requests

### 4. Grayscale Publishing
- Support for grayscale deployment based on version tags
- Support for grayscale publishing based on request headers

### 5. Load Balancing
- Service instance load balancing
- Weight-based routing selection

## Quick Start

### Environment Requirements
- JDK 8+
- Maven 3.5+
- Nacos service

### Configuration
Modify the Nacos configuration in `bootstrap-{profile}.yaml`: