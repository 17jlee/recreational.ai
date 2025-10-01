# SSL Certificates

This directory contains SSL certificates for HTTPS support on the backend server.

## Self-Signed Certificates (Development)

The current certificates (`cert.pem` and `key.pem`) are self-signed and intended for local development only.

### Generating New Self-Signed Certificates

If you need to regenerate the certificates, run:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

### Browser Warnings

When using self-signed certificates, browsers will show security warnings. This is expected behavior:

- **Chrome/Edge**: Click "Advanced" → "Proceed to localhost (unsafe)"
- **Firefox**: Click "Advanced" → "Accept the Risk and Continue"
- **Safari**: Click "Show Details" → "visit this website"

## Production Certificates

For production deployment, replace the self-signed certificates with proper SSL certificates from a Certificate Authority (CA) such as:

- Let's Encrypt (free)
- DigiCert
- Comodo
- Others

### Using Let's Encrypt

For production servers, you can use [Certbot](https://certbot.eff.org/) to obtain free SSL certificates:

```bash
sudo certbot certonly --standalone -d yourdomain.com
```

Then update the certificate paths in `app.py` to point to the Let's Encrypt certificates.

## Security Notes

- Certificate files (*.pem, *.key, *.crt) are excluded from git via `.gitignore`
- Never commit private keys to version control
- Regenerate certificates periodically (at least annually)
- For production, use certificates from a trusted CA
