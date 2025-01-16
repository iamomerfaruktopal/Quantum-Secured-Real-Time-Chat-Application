# Quantum-Secured Real-Time Chat Application

A secure chat application implementing quantum-inspired cryptography with automatic key rotation and real-time message encryption. This project demonstrates advanced security concepts including quantum key distribution simulation, automatic session management, and encrypted real-time communication.

## Features

### Security
- Quantum-inspired key generation and distribution
- Automatic 20-second key rotation cycles
- AES-GCM encryption for all messages
- Session-based secure communication
- Protection against replay attacks
- Manual decryption verification

### Communication
- Real-time WebSocket-based messaging
- Bidirectional encrypted communication
- Session management with unique IDs
- Visual key rotation countdown
- Message encryption status indicators

### User Interface
- Clean, intuitive chat interface
- Encryption/decryption status display
- Session timer visualization
- Secure connection indicators
- Real-time key rotation notifications

## Technology Stack

### Backend
- FastAPI (Python web framework)
- WebSocket for real-time communication
- Qiskit for quantum-inspired operations
- Cryptography library for encryption

### Frontend
- Pure JavaScript (No external dependencies)
- WebSocket API
- Web Crypto API
- Modern CSS3

### Security
- AES-GCM encryption
- Quantum key distribution simulation
- SSL/TLS with auto-certificate generation
- Session-based authentication

## Installation

1. Clone the Repository:
   git clone https://github.com/yourusername/Quantum-Secured-Real-Time-Chat-Application.git
   cd quantum-secure-chat

2. Set Up Virtual Environment:
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install Dependencies:
   pip install -r requirements.txt

4. Run the Application:
   python main.py

5. Access the Application:
   - Open https://localhost:8000 in your browser
   - Accept the self-signed certificate for development

## Usage

1. Start the Application
   - Launch two browser windows (simulating two parties)
   - Each window represents a different user

2. Establish Connection
   - Enter unique identifiers for each user
   - Click "Connect" to join the secure network

3. Initialize Secure Channel
   - Enter partner's ID in one window
   - Start key exchange process
   - Wait for quantum key generation

4. Send Encrypted Messages
   - Type message in the input field
   - Messages are automatically encrypted
   - Key rotation occurs every 20 seconds

5. Decrypt Messages
   - Click "Decrypt" button on received messages
   - View the decrypted content
   - Verify encryption status

## Security Implementation

### Quantum Key Generation
- Simulated quantum state preparation
- Random basis selection
- Key verification process

### Encryption Process
- AES-GCM for message encryption
- Unique IV for each message
- Automatic key rotation

### Session Management
- Unique session identifiers
- Automatic session expiration
- Secure key storage

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch: git checkout -b feature/AmazingFeature
3. Commit your changes: git commit -m 'Add some AmazingFeature'
4. Push to the branch: git push origin feature/AmazingFeature
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI framework for efficient API development
- Qiskit for quantum computing concepts
- Cryptography library for secure operations
- WebSocket protocol for real-time communication

## Contact

Ömer Faruk Topal - @iamomerfaruktopal
Personal Website: https://web.itu.edu.tr/topalo24/
Project Link: https://github.com/iamomerfaruktopal/Quantum-Secured-Real-Time-Chat-Application