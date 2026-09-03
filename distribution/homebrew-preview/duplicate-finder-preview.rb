class DuplicateFinderPreview < Formula
  include Language::Python::Virtualenv

  desc "Preview build: desktop application for finding and removing duplicate files"
  homepage "https://github.com/denis-peshkov/duplicate-finder"
  version "0.0.0"
  url "https://github.com/denis-peshkov/duplicate-finder/archive/0000000000000000000000000000000000000000.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    system venv/"bin/pip", "install", buildpath.to_s
    bin.install_symlink libexec/"bin/duplicate-finder"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/duplicate-finder --version")
  end
end
