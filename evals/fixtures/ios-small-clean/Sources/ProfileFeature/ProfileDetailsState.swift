public enum ProfileDetailsState: Equatable, Sendable {
  case loading
  case content(Profile)
  case failure(message: String)
}
