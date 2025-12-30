# MAX-DETOX-LIFESTYLE-BLACKOUT v1.0

## The Manifesto

In a world where corporations exploit our psychology for profit, this project stands as a digital shield against unhealthy lifestyle enablers and financial blackholes. These blocklists help you reclaim control over your attention, health, and finances by blocking domains that promote:

- **Ultra-processed foods** that damage your health
- **Predatory delivery services** that drain your wallet
- **Beauty industry manipulation** that preys on insecurity
- **Mega-conglomerates** that control markets and choices

This is not just about blocking websites—it's about reclaiming autonomy over your digital life and breaking free from engineered consumption patterns.

## Project Structure

```
/ (root)
├── README.md             # The "Manifesto" (Explains what this is and why)
├── food.txt              # Purely fast food, delivery, and snacks
├── cosmetics.txt         # Beauty brands and predatory cosmetic promoters
├── conglomerates.txt     # The "Nuclear" list (Nestle, Unilever, etc.)
├── blackout-ultra.txt    # A master file that includes all of the above
└── .gitignore            # Standard GitHub housekeeping
```

## Blocklists

### 🍔 food.txt
Fast food chains, delivery platforms, and ultra-processed food companies.

**Includes:** McDonald's, Burger King, KFC, Taco Bell, Pizza Hut, Domino's, Subway, Wendy's, DoorDash, UberEats, GrubHub, Postmates

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/food.txt
```

### 💄 cosmetics.txt
Beauty retailers and brands that promote overconsumption and unrealistic standards.

**Includes:** Sephora, Ulta, L'Oréal, Estée Lauder, MAC, Clinique, Maybelline, CoverGirl, Revlon

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/cosmetics.txt
```

### 🏢 conglomerates.txt
The "Nuclear" option - Major corporations that dominate markets and control consumer choices.

**Includes:** Nestlé, Unilever, Procter & Gamble, Coca-Cola, PepsiCo (and their numerous subsidiary brands)

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/conglomerates.txt
```

### ☢️ blackout-ultra.txt
The master list combining ALL categories above. Use this for maximum protection.

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/blackout-ultra.txt
```

## How to Use

### Installing in Pi-hole

1. Log in to your Pi-hole admin interface
2. Navigate to **Group Management** → **Adlists**
3. Add one or more blocklist URLs from above
4. Click **Add** for each list
5. Go to **Tools** → **Update Gravity** to apply changes

### Choosing Your Level

- **Light Mode**: Use `food.txt` only to block food delivery temptations
- **Medium Mode**: Use `food.txt` + `cosmetics.txt` to also avoid beauty marketing
- **Heavy Mode**: Use `food.txt` + `cosmetics.txt` + `conglomerates.txt` individually
- **Nuclear Mode**: Use `blackout-ultra.txt` for complete coverage

## Philosophy

We believe in:
- **Digital minimalism** - Less is more
- **Conscious consumption** - Buy what you need, not what you're sold
- **Health over convenience** - Your body deserves better than delivery junk
- **Independence** - Breaking free from corporate manipulation

## Contributing

Found a domain that should be blocked? Open an issue or submit a pull request. Let's build this together.

## Disclaimer

These blocklists are provided as-is for personal use. Users are solely responsible for their own network filtering decisions. This project does not endorse or condemn any specific company—it simply provides tools for those seeking to reduce exposure to certain types of marketing and services.

## License

Public domain. Use freely, modify freely, share freely. 
