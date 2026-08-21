from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext
from app.services.banking_service import BankingService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> User:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create new user"""
        db_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            address=user.address,
            date_of_birth=user.date_of_birth,
            password_hash=UserService.hash_password(user.password)
        )
        db.add(db_user)
        db.flush()
        BankingService.ensure_primary_account(db, db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user"""
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            return None
        
        update_fields = user_update.model_fields_set

        if "full_name" in update_fields:
            db_user.full_name = user_update.full_name
        if "phone" in update_fields:
            db_user.phone = user_update.phone
        if "address" in update_fields:
            db_user.address = user_update.address
        if "date_of_birth" in update_fields:
            db_user.date_of_birth = user_update.date_of_birth
        if "password" in update_fields and user_update.password is not None:
            db_user.password_hash = UserService.hash_password(user_update.password)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete user"""
        db_user = UserService.get_user(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 10) -> list:
        """List all users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()
