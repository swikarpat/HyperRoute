# Multi-stage Dockerfile for HyperRoute Spring Cloud Gateway
FROM gradle:8.10-jdk21 AS build

WORKDIR /workspace
COPY . .
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre

RUN useradd -u 10001 -m -s /bin/bash hyperroute
WORKDIR /app

COPY --from=build --chown=hyperroute:hyperroute /workspace/build/libs/*.jar app.jar

USER hyperroute
EXPOSE 8080

ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -Djava.security.egd=file:/dev/./urandom"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]