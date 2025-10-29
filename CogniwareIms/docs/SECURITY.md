# Security Policy

## Overview

Security is a top priority for the Cogniware OPEA IMS project. This document outlines our security practices and guidelines for deploying and using the system securely.

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. Email security concerns to: [security@cogniware.com](mailto:security@cogniware.com)
3. Include detailed information about the vulnerability
4. Allow us reasonable time to respond and fix the issue

## Security Features

### Authentication & Authorization

- ✅ JWT-based authentication with configurable expiration
- ✅ Password hashing using bcrypt (industry standard)
- ✅ Role-based access control (RBAC)
- ✅ Secure password requirements (minimum 8 characters)
- ✅ Session management and timeout

### Data Protection

- ✅ HTTPS/TLS encryption support
- ✅ Secure headers (CSP, HSTS, X-Frame-Options, etc.)
- ✅ SQL injection prevention via parameterized queries
- ✅ Input validation and sanitization
- ✅ XSS protection

### API Security

- ✅ CORS protection with configurable origins
- ✅ Rate limiting to prevent abuse
- ✅ Request size limits
- ✅ API authentication required for sensitive endpoints

### Infrastructure Security

- ✅ Non-root user execution in containers
- ✅ Resource limits to prevent DoS
- ✅ Health checks and monitoring
- ✅ Secure secrets management via environment variables
- ✅ Network isolation via Docker networks

## Production Deployment Checklist

### Critical (Before Going Live)

- [ ] **Change all default passwords**
  - PostgreSQL admin password
  - Default user passwords
  - Grafana admin password

- [ ] **Generate strong JWT secret**
  ```bash
  openssl rand -hex 32
  ```
  Update `JWT_SECRET_KEY` in `.env`

- [ ] **Enable HTTPS/TLS**
  - Obtain SSL certificates (Let's Encrypt recommended)
  - Configure nginx with HTTPS
  - Force HTTPS redirects
  - Enable HSTS header

- [ ] **Configure CORS properly**
  - Set specific allowed origins (not `*`)
  - Update `ALLOWED_ORIGINS` in `.env`

- [ ] **Update default credentials**
  - Create new admin users with strong passwords
  - Remove or disable default demo users

### Recommended

- [ ] **Enable rate limiting**
  - Configure `RATE_LIMIT_PER_MINUTE` appropriately
  - Monitor for abuse patterns

- [ ] **Set up firewall rules**
  - Only expose necessary ports (80, 443)
  - Restrict database ports (5432, 6379) to internal network
  - Block direct access to OPEA services from internet

- [ ] **Enable audit logging**
  - Configure centralized logging
  - Set up log rotation and retention
  - Monitor for suspicious activities

- [ ] **Regular backups**
  - Database backups (PostgreSQL)
  - Redis snapshots
  - Knowledge base exports
  - Disaster recovery plan

- [ ] **Security updates**
  - Regularly update Docker images
  - Monitor CVE databases
  - Update dependencies (`pip-audit`, `npm audit`)

- [ ] **Access control**
  - Implement principle of least privilege
  - Use separate credentials for different environments
  - Rotate credentials periodically

## Secure Configuration

### Environment Variables

**Never commit `.env` files to version control!**

Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### Minimum Password Requirements

Enforced by the system:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- (Optional) Special characters

### JWT Token Configuration

```env
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Security

```env
# Use strong passwords
POSTGRES_PASSWORD=<strong-random-password>

# Connection string with credentials
DATABASE_URL=postgresql://postgres:<password>@postgres:5432/opea_ims
```

## Network Security

### Docker Network Isolation

Services are isolated in `opea-network`:
- Frontend/Backend can communicate
- OPEA services communicate internally
- Databases not exposed externally

### Exposed Ports (Production)

```yaml
# External (via nginx)
80:   HTTP (redirect to HTTPS)
443:  HTTPS

# Internal only (block external access)
5432: PostgreSQL
6379: Redis
6000: Embedding Service
7000: Retrieval Service
9000: LLM Service
8888: OPEA Gateway
```

## Monitoring & Incident Response

### Security Monitoring

Monitor logs for:
- Failed login attempts
- Unusual API usage patterns
- SQL injection attempts
- XSS attempts
- Rate limit violations
- Unexpected errors

### Log Files

```bash
# View security-related logs
docker-compose logs backend | grep "SECURITY_EVENT"
docker-compose logs nginx | grep "403\|404\|500"
```

### Incident Response

If security breach detected:

1. **Immediate**
   - Isolate affected systems
   - Change all credentials
   - Review logs for compromise extent

2. **Investigation**
   - Identify attack vector
   - Assess data exposure
   - Document timeline

3. **Remediation**
   - Patch vulnerabilities
   - Update security policies
   - Notify affected users if required

4. **Prevention**
   - Implement additional controls
   - Update documentation
   - Train team members

## Best Practices

### Development

- Use separate dev/staging/production environments
- Never use production credentials in development
- Run security scanners regularly
- Keep dependencies updated
- Follow secure coding guidelines

### Deployment

- Use infrastructure-as-code (IaC)
- Automated security testing in CI/CD
- Immutable infrastructure
- Regular penetration testing

### Operations

- Principle of least privilege
- Multi-factor authentication for admins
- Regular security audits
- Incident response plan
- Data retention policies

## Compliance

This system supports compliance with:

- **GDPR**: Data protection and privacy
- **SOC 2**: Security controls and monitoring
- **ISO 27001**: Information security management
- **HIPAA**: Healthcare data protection (with additional configuration)

Specific compliance requirements may need additional configuration.

## Security Tools

### Recommended Tools

**Vulnerability Scanning:**
```bash
# Python dependencies
pip-audit

# Docker images
docker scan cogniware-opea-ims-backend

# npm dependencies
npm audit
```

**Secret Detection:**
```bash
# Scan for committed secrets
git-secrets --scan
trufflehog
```

**SAST (Static Analysis):**
```bash
# Python
bandit -r backend/

# TypeScript/JavaScript
eslint frontend/ --ext .ts,.tsx
```

**DAST (Dynamic Analysis):**
```bash
# OWASP ZAP
zap-baseline.py -t http://localhost:3000
```

## Updates & Patches

### Update Schedule

- **Critical**: Within 24 hours
- **High**: Within 1 week
- **Medium**: Within 1 month
- **Low**: Next release cycle

### Update Process

```bash
# Pull latest images
docker-compose pull

# Rebuild with updates
docker-compose build --no-cache

# Deploy with zero downtime
docker-compose up -d --no-deps --build <service>
```

## Data Protection

### Encryption

- **In Transit**: HTTPS/TLS 1.2+
- **At Rest**: Database encryption (configure PostgreSQL)
- **Secrets**: Environment variables, not hardcoded

### Data Retention

- Configure based on requirements
- Implement data deletion policies
- Regular data cleanup

### Privacy

- Minimize data collection
- Anonymize where possible
- User consent for data processing
- Right to deletion support

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Security Headers](https://nextjs.org/docs/advanced-features/security-headers)

## Contact

For security questions or concerns:
- Email: security@cogniware.com
- Documentation: See `docs/security/` directory

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update security measures.

