# One Piece Character Tracker 🏴‍☠️

A web application that tracks One Piece character values over time, showing how character importance and "stock market value" changes throughout the manga chapters.

![One Piece Character Tracker](https://img.shields.io/badge/One%20Piece-Character%20Tracker-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Flask](https://img.shields.io/badge/Flask-Web%20App-red)
![Chart.js](https://img.shields.io/badge/Chart.js-Interactive%20Charts-orange)

## 🌟 Features

- **Character Value Tracking**: View current values and historical changes for One Piece characters
- **Interactive Charts**: Compare multiple characters with hover tooltips showing detailed reasoning
- **Search & Filter**: Find characters by name, value range, or introduction era
- **Mobile Responsive**: Optimized for all device sizes
- **Real-time Data**: Character values based on manga chapter analysis

## 📊 Screenshots

### Character List
Browse all characters with their current values and first appearances.

### Individual Character Pages
Detailed view with value history charts and related characters.

### Multi-Character Comparison
Interactive charts comparing multiple characters over time.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/one-piece-character-tracker.git
   cd one-piece-character-tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5001`

## 🐳 Docker Deployment

### Simple Docker
```bash
./deploy.sh docker
```

### Production with Nginx
```bash
./deploy.sh docker-prod
```

## 📱 Mobile Support

The application is fully responsive and optimized for:
- Desktop browsers
- Tablets
- Mobile phones
- Touch interactions

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js
- **Styling**: Custom CSS with responsive design
- **Deployment**: Docker, Docker Compose, Nginx

## 📈 Data Structure

The application tracks:
- **Characters**: Name, current value, first appearance chapter
- **Character History**: Value changes over time with reasoning
- **Chapters**: Chapter information and titles

## 🔧 Configuration

### Environment Variables
- `FLASK_ENV`: Set to 'production' for production deployment
- `SECRET_KEY`: Change this in production
- `DATABASE_PATH`: Path to SQLite database file
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5001)

### Production Setup
1. Copy `.env.example` to `.env.production`
2. Update the SECRET_KEY
3. Set FLASK_ENV=production

## 🧪 Testing

Run the verification script to test all functionality:
```bash
python verify_app.py
```

## 📦 Deployment Options

### 1. Local Development
```bash
./deploy.sh local
```

### 2. Docker Container
```bash
./deploy.sh docker
```

### 3. Production with Nginx
```bash
./deploy.sh docker-prod
```

### 4. Cloud Deployment (Render, Heroku, etc.)
See deployment instructions in the docs.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Eiichiro Oda for creating One Piece
- The One Piece Wiki community
- Chart.js for excellent charting library
- Flask community for the web framework

## 📞 Support

If you have any questions or issues:
1. Check the [Issues](https://github.com/yourusername/one-piece-character-tracker/issues) page
2. Create a new issue if needed
3. Provide detailed information about your problem

---

**Disclaimer**: This is a fan project and is not affiliated with Eiichiro Oda or Shueisha. One Piece is the property of Eiichiro Oda.