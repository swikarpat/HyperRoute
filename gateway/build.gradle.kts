import com.google.protobuf.gradle.*

plugins {
    java
    id("org.springframework.boot") version "3.3.3"
    id("io.spring.dependency-management") version "1.1.6"
    id("com.google.protobuf") version "0.9.4"
}

group = "com.apexgateway"
version = "1.0.0"

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

repositories {
    mavenCentral()
}

val grpcVersion = "1.66.0"
val protobufVersion = "3.25.3"

dependencies {
    // Spring Boot Reactive Web
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    implementation("org.springframework.boot:spring-boot-starter-actuator")

    // Resilience & Fault Tolerance
    implementation("io.github.resilience4j:resilience4j-spring-boot3:2.2.0")
    implementation("io.github.resilience4j:resilience4j-reactor:2.2.0")
    implementation("org.springframework.boot:spring-boot-starter-aop")

    // gRPC & Protobuf
    implementation("io.grpc:grpc-netty-shaded:$grpcVersion")
    implementation("io.grpc:grpc-protobuf:$grpcVersion")
    implementation("io.grpc:grpc-stub:$grpcVersion")
    implementation("com.google.protobuf:protobuf-java:$protobufVersion")

    // Provides javax.annotation.Generated for protoc-gen-grpc-java on JDK 11/17/21
    compileOnly("org.apache.tomcat:annotations-api:6.0.53")
    compileOnly("jakarta.annotation:jakarta.annotation-api:2.1.1")

    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("io.projectreactor:reactor-test")
}

sourceSets {
    main {
        proto {
            srcDir("../apexgateway-contracts/proto")
        }
    }
}

protobuf {
    protoc {
        artifact = "com.google.protobuf:protoc:$protobufVersion"
    }
    plugins {
        id("grpc") {
            artifact = "io.grpc:protoc-gen-grpc-java:$grpcVersion"
        }
    }
    generateProtoTasks {
        ofSourceSet("main").forEach {
            it.plugins {
                id("grpc")
            }
        }
    }
}