// swift-tools-version: 6.0

import PackageDescription

let package = Package(
  name: "MobileFixture",
  platforms: [
    .iOS(.v16),
    .macOS(.v13),
  ],
  products: [
    .library(name: "ProfileFeature", targets: ["ProfileFeature"])
  ],
  targets: [
    .target(name: "ProfileFeature"),
    .testTarget(name: "ProfileFeatureTests", dependencies: ["ProfileFeature"]),
  ]
)
