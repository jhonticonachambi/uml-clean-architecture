# app/application/services/converters/java/sequence_converter.py
class JavaSequenceConverter:
    def convert(self, code: str) -> str:
        plantuml = ["@startuml"]
        
        if ".method" in code.lower() or "(" in code and ")" in code:
            plantuml.append("User -> Controller : processRequest()")
            plantuml.append("Controller -> Service : validate()")
            plantuml.append("Service --> Controller : validationResult")
            plantuml.append("Controller --> User : response")
        else:
            plantuml.append("participant A")
            plantuml.append("participant B")
            plantuml.append("A -> B : message()")
        
        plantuml.append("@enduml")
        return "\n".join(plantuml)