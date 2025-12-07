# FatSecret API Setup

## Get Your API Credentials

1. Go to https://platform.fatsecret.com/api/
2. Click "Get Started" or "Sign Up"
3. Create a free developer account
4. Create a new application
5. You'll receive:
   - Client ID
   - Client Secret
   - Free tier: Good for development and testing

## Add to .env File

Add these lines to your `.env` file:

```
FATSECRET_CLIENT_ID=your_client_id_here
FATSECRET_CLIENT_SECRET=your_client_secret_here
```

## Features

- Large food database with branded and restaurant foods
- OAuth2 authentication (handled automatically)
- Good accuracy for common dishes
- Free tier available

## Test the API

The nutrition endpoint is at:
```
GET /catalog/meals/{meal_id}/nutrition
```

Example response:
```json
{
  "meal_name": "Grilled Chicken Salad",
  "calories": 280,
  "protein_g": 35.0,
  "carbs_g": 12.0,
  "fat_g": 10.0,
  "fiber_g": 4.0,
  "sugar_g": 6.0,
  "sodium_mg": 450.0
}
```

## Fallback

If API credentials are not configured, the service automatically falls back to estimated nutrition data.
