import sys
from loguru import logger

def setup_logger():
    """Configure and set up the logger."""
    logger.remove()  # Remove default handler
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,  # Changed to stdout for better terminal visibility
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
               "<level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Add file handler
    logger.add(
        "github_maintainer.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG"
    )
    
    return logger

def get_logger(name: str = __name__):
    """Get a logger instance for the specified name."""
    return logger.bind(name=name)
