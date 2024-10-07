from typing import Any, Optional

class Animal:
    def ___init__(self,
            animal_id: int,
            species: str,
            health_status: Optional[str] = None,
            age: Optional[int] = None) -> None:
        self.animal_id = animal_id
        self.species = species
        self.health_status = health_status
        self.age = age
    
    def get_animal_details(self) -> dict[str, Any]:
        pass
    
    def update_animal_details(self, **kwargs: Any) -> None:
        pass