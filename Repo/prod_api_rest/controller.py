import json
from typing import Dict, Any, Tuple
from repository import Repository




def main()-> None:
    
    repo= Repository()
    data= repo.get_client_data('A00000006')
    print(data)

if __name__ == "__main__":    
    main()


