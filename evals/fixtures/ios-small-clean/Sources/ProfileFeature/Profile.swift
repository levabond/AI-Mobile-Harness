public struct Profile: Equatable, Sendable {
  public let displayName: String
  public let handle: String
  public let biography: String

  public init(displayName: String, handle: String, biography: String) {
    self.displayName = displayName
    self.handle = handle
    self.biography = biography
  }
}
